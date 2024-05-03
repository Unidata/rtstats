#!/usr/bin/env python
"""Emit GeoJSON of IDD topology

    /services/idd.geojson?feedtype=<feedtype>

This service is cached for 3 minutes via memcached
"""

import datetime
import json

import memcache
import pytz
import rtstats_util as util
from paste.request import parse_formvars


def run(feedtype):
    """Generate geojson for this feedtype"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    sts = datetime.datetime.utcnow()
    cursor.execute(
        """
    with data as (
        select relay_host_id, node_host_id,
        avg_latency,
        r.entry_added,
        rank() OVER
            (PARTITION by r.feedtype_path_id ORDER by r.entry_added DESC)
        from ldm_rtstats r JOIN ldm_feedtype_paths p
            on (r.feedtype_path_id = p.id)
        WHERE r.entry_added > now() - '15 minutes'::interval
        and p.feedtype_id = get_ldm_feedtype_id(%s)),
    agg1 as (
        SELECT relay_host_id, node_host_id, avg(avg_latency) as avg_latency,
        max(entry_added) as valid
        from data WHERE rank = 1 GROUP by relay_host_id, node_host_id),
    geos as (
        SELECT st_makeline(
    (SELECT geom from ldm_hostnames where id = a.relay_host_id),
    (SELECT geom from ldm_hostnames where id = a.node_host_id)) as geom,
    (SELECT hostname from ldm_hostnames where id = a.relay_host_id) as relay,
    (SELECT hostname from ldm_hostnames where id = a.node_host_id) as node,
        avg_latency,
        valid
        from agg1 a)

    SELECT ST_asGEoJSON(geom, 2), relay, node, avg_latency,
    to_char(valid at time zone 'UTC', 'YYYY-MM-DDThh24:MI:SSZ') from geos
    WHERE geom is not null and ST_Length(geom) > 0.1
    """,
        (feedtype,),
    )
    utcnow = datetime.datetime.utcnow()
    res = {
        "type": "FeatureCollection",
        "crs": {
            "type": "EPSG",
            "properties": {"code": 4326, "coordinate_order": [1, 0]},
        },
        "features": [],
        "generation_time": utcnow.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query_time[secs]": (utcnow - sts).total_seconds(),
        "count": cursor.rowcount,
    }
    for i, row in enumerate(cursor):
        if row[0] is None:
            continue
        res["features"].append(
            dict(
                type="Feature",
                id=i,
                properties=dict(
                    latency=row[3], relay=row[1], node=row[2], utc_valid=row[4]
                ),
                geometry=json.loads(row[0]),
            )
        )

    return json.dumps(res)


def stats():
    """Overview stats"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    sts = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    if sts.minute < 20:  # Assume we have last hours stats by :20 after
        sts -= datetime.timedelta(hours=1)
    sts = sts.replace(minute=0, second=0, microsecond=0, tzinfo=pytz.utc)
    cursor.execute(
        """
        SELECT sum(nbytes)::bigint from ldm_rtstats_hourly
        WHERE valid = %s
    """,
        (sts,),
    )
    nbytes = cursor.fetchone()[0]
    cursor.execute(
        """
        select count(distinct node_host_id)::bigint from
        ldm_rtstats_hourly h JOIN ldm_feedtype_paths p on
        (h.feedtype_path_id = p.id) WHERE h.valid = %s
    """,
        (sts,),
    )
    hosts = cursor.fetchone()[0]
    res = dict()
    res["generation_time"] = datetime.datetime.utcnow().strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    res["data"] = [
        dict(
            valid=sts.strftime("%Y-%m-%dT%H:%M:00Z"),
            nbytes=nbytes,
            hosts=hosts,
        )
    ]

    return json.dumps(res)


def application(environ, start_response):
    """Answer request."""
    fields = parse_formvars(environ)

    feedtype = fields.get("feedtype", "IDS|DDPLUS").upper()[:32]
    cb = fields.get("callback")
    service = fields.get("service", "geojson")
    mckey = "/services/idd.py?service=%s&feedtype=%saa" % (service, feedtype)
    mc = memcache.Client(["localhost:11211"], debug=0)
    res = mc.get(mckey)
    if not res:
        if service == "geojson":
            res = run(feedtype)
            expire = 180
        else:
            res = stats()
            expire = 3600
        mc.set(mckey, res, expire)
    if cb is None:
        data = res
    else:
        data = "%s(%s)" % (cb, res)

    headers = [("Content-type", "application/vnd.geo+json")]
    start_response("200 OK", headers)
    return [data.encode("ascii", "ignore")]
