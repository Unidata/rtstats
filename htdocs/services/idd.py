#!/usr/bin/env python
"""Emit GeoJSON of IDD topology

    /services/idd.geojson?feedtype=<feedtype>

This service is cached for 3 minutes via memcached
"""
import memcache
import cgi
import sys
import rtstats_util as util


def run(feedtype):
    """Generate geojson for this feedtype"""
    import json
    import datetime

    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    sts = datetime.datetime.utcnow()
    cursor.execute("""
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
    """, (feedtype, ))
    utcnow = datetime.datetime.utcnow()
    res = {'type': 'FeatureCollection',
           'crs': {'type': 'EPSG',
                   'properties': {'code': 4326, 'coordinate_order': [1, 0]}},
           'features': [],
           'generation_time': utcnow.strftime("%Y-%m-%dT%H:%M:%SZ"),
           'query_time[secs]': (utcnow - sts).total_seconds(),
           'count': cursor.rowcount}
    for i, row in enumerate(cursor):
        if row[0] is None:
            continue
        res['features'].append(dict(type="Feature",
                                    id=i,
                                    properties=dict(
                                        latency=row[3],
                                        relay=row[1],
                                        node=row[2],
                                        utc_valid=row[4]
                                        ),
                                    geometry=json.loads(row[0])
                                    ))

    return json.dumps(res)


def main():
    """Go Main Go"""
    sys.stdout.write("Content-type: application/vnd.geo+json\n\n")
    form = cgi.FieldStorage()
    feedtype = form.getfirst('feedtype', 'IDS|DDPLUS').upper()[:32]
    cb = form.getfirst('callback', None)
    mckey = "/services/idd.geojson?feedtype=%s" % (feedtype,)
    mc = memcache.Client(['memcached.local:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = run(feedtype)
        mc.set(mckey, res, 180)
    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))

if __name__ == '__main__':
    main()
