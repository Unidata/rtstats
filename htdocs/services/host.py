#!/usr/bin/env python
"""Emit JSON of host

    /services/host/<hostname>/feedtypes.json
    /services/host/<hostname>/rtstats.json
    /services/host/<hostname>/topology.json

"""
import collections
import datetime
import json

import memcache
import pandas as pd
from paste.request import parse_formvars
import rtstats_util as util


def Tree():
    """Make me a tree"""
    return collections.defaultdict(Tree)


def handle_rtstats(hostname, feedtype):
    """Emit JSON for rtstats for this host"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    flimit = ""
    if feedtype != "":
        flimit = " and p.feedtype_id = get_ldm_feedtype_id('%s') " % (
            feedtype,
        )
    sts = datetime.datetime.utcnow()
    cursor.execute(
        """
    select
    to_char(r.entry_added at time zone 'UTC', 'YYYY-MM-DDThh24:MI:SSZ'),
    r.feedtype_path_id,
    (select hostname from ldm_hostnames where id = p.origin_host_id) as origin,
    (select hostname from ldm_hostnames where id = p.relay_host_id) as relay,
    avg_latency,
    (select feedtype from ldm_feedtypes where id = p.feedtype_id) as feedtype
    from ldm_rtstats r JOIN ldm_feedtype_paths p on
    (r.feedtype_path_id = p.id) WHERE
    p.node_host_id = get_ldm_host_id(%s) and
    r.entry_added > now() - '36 hours'::interval """
        + flimit
        + """
    ORDER by r.entry_added ASC
    """,
        (hostname,),
    )
    utcnow = datetime.datetime.utcnow()
    res = dict()
    res["query_time[secs]"] = (utcnow - sts).total_seconds()
    res["hostname"] = hostname
    res["columns"] = [
        "entry_added",
        "feedtype_path_id",
        "origin",
        "relay",
        "avg_latency",
        "feedtype",
    ]
    res["data"] = []
    for row in cursor:
        res["data"].append(row)
    return json.dumps(res)


def handle_weekly(hostname, feedtype, since):
    """Emit JSON for rtstats for this host"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    flimit = ""
    if feedtype != "":
        flimit = " and p.feedtype_id = get_ldm_feedtype_id('%s') " % (
            feedtype,
        )
    tlimit = ""
    if since is not None:
        tlimit = (" and h.valid >= '%s' ") % (
            pd.to_datetime(since).strftime("%Y-%m-%d"),
        )
    sts = datetime.datetime.utcnow()
    cursor.execute(
        """
    WITH weekly as (
        SELECT
        extract(isoyear from valid) as yr, extract(week from valid) as week,
        feedtype_path_id,
        min(min_latency) as min_latency, avg(avg_latency) as avg_latency,
        max(max_latency) as max_latency, sum(nprods) as nprods,
        sum(nbytes) as nbytes,
        max(feedtype_id) as feedtype_id from
        ldm_rtstats_daily h JOIN ldm_feedtype_paths p on
            (h.feedtype_path_id = p.id) WHERE
        p.node_host_id = get_ldm_host_id(%s) """
        + flimit
        + """
        """
        + tlimit
        + """ GROUP by yr, week, feedtype_path_id)
    select
    to_char(
        (yr || '-01-01')::date + (week || ' weeks')::interval, 'YYYY-mm-dd')
        as v,
    h.feedtype_path_id,
    (select hostname from ldm_hostnames where id = p.origin_host_id) as origin,
    (select hostname from ldm_hostnames where id = p.relay_host_id) as relay,
    min_latency,
    avg_latency,
    max_latency,
    nprods::bigint,
    nbytes::bigint,
    (select feedtype from ldm_feedtypes where id = p.feedtype_id) as feedtype
    from weekly h JOIN ldm_feedtype_paths p on
    (h.feedtype_path_id = p.id)
    ORDER by v ASC
    """,
        (hostname,),
    )
    utcnow = datetime.datetime.utcnow()
    res = dict()
    res["query_time[secs]"] = (utcnow - sts).total_seconds()
    res["hostname"] = hostname
    res["columns"] = [
        "valid",
        "feedtype_path_id",
        "origin",
        "relay",
        "min_latency",
        "avg_latency",
        "max_latency",
        "nprods",
        "nbytes",
        "feedtype",
    ]
    res["data"] = []
    for row in cursor:
        res["data"].append(row)
    return json.dumps(res)


def handle_daily(hostname, feedtype, since):
    """Emit JSON for rtstats for this host"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    flimit = ""
    if feedtype != "":
        flimit = " and p.feedtype_id = get_ldm_feedtype_id('%s') " % (
            feedtype,
        )
    tlimit = ""
    if since is not None:
        tlimit = (" and h.valid >= '%s' ") % (
            pd.to_datetime(since).strftime("%Y-%m-%d"),
        )
    sts = datetime.datetime.utcnow()
    cursor.execute(
        """
    select
    to_char(valid, 'YYYY-MM-DD'),
    h.feedtype_path_id,
    (select hostname from ldm_hostnames where id = p.origin_host_id) as origin,
    (select hostname from ldm_hostnames where id = p.relay_host_id) as relay,
    min_latency,
    avg_latency,
    max_latency,
    nprods,
    nbytes,
    (select feedtype from ldm_feedtypes where id = p.feedtype_id) as feedtype
    from ldm_rtstats_daily h JOIN ldm_feedtype_paths p on
    (h.feedtype_path_id = p.id) WHERE
    p.node_host_id = get_ldm_host_id(%s) """
        + flimit
        + """
    """
        + tlimit
        + """
    ORDER by h.valid ASC
    """,
        (hostname,),
    )
    utcnow = datetime.datetime.utcnow()
    res = dict()
    res["query_time[secs]"] = (utcnow - sts).total_seconds()
    res["hostname"] = hostname
    res["columns"] = [
        "valid",
        "feedtype_path_id",
        "origin",
        "relay",
        "min_latency",
        "avg_latency",
        "max_latency",
        "nprods",
        "nbytes",
        "feedtype",
    ]
    res["data"] = []
    for row in cursor:
        res["data"].append(row)
    return json.dumps(res)


def handle_hourly(hostname, feedtype, since):
    """Emit JSON for rtstats for this host"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    flimit = ""
    if feedtype != "":
        flimit = " and p.feedtype_id = get_ldm_feedtype_id('%s') " % (
            feedtype,
        )
    tlimit = ""
    if since is not None:
        tlimit = (" and h.valid >= '%s' ") % (
            pd.to_datetime(since).strftime("%Y-%m-%d %H:%M+00"),
        )
    sts = datetime.datetime.utcnow()
    cursor.execute(
        """
    select
    to_char(valid at time zone 'UTC', 'YYYY-MM-DDThh24:MI:SSZ'),
    h.feedtype_path_id,
    (select hostname from ldm_hostnames where id = p.origin_host_id) as origin,
    (select hostname from ldm_hostnames where id = p.relay_host_id) as relay,
    min_latency,
    avg_latency,
    max_latency,
    nprods,
    nbytes,
    (select feedtype from ldm_feedtypes where id = p.feedtype_id) as feedtype
    from ldm_rtstats_hourly h JOIN ldm_feedtype_paths p on
    (h.feedtype_path_id = p.id) WHERE
    p.node_host_id = get_ldm_host_id(%s) """
        + flimit
        + """
    """
        + tlimit
        + """
    ORDER by h.valid ASC
    """,
        (hostname,),
    )
    utcnow = datetime.datetime.utcnow()
    res = dict()
    res["query_time[secs]"] = (utcnow - sts).total_seconds()
    res["hostname"] = hostname
    res["columns"] = [
        "valid",
        "feedtype_path_id",
        "origin",
        "relay",
        "min_latency",
        "avg_latency",
        "max_latency",
        "nprods",
        "nbytes",
        "feedtype",
    ]
    res["data"] = []
    for row in cursor:
        res["data"].append(row)
    return json.dumps(res)


def handle_topology(hostname, feedtype):
    """Generate topology for this feedtype"""
    if feedtype == "":
        return json.dumps("NO_FEEDTYPE_SET_ERROR")
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    # compute all upstreams for this feedtype
    upstreams = {}
    sts = datetime.datetime.utcnow()
    cursor.execute(
        """
    WITH active as (
        select distinct id from
        ldm_feedtype_paths p JOIN ldm_rtstats_hourly r
        on (p.id = r.feedtype_path_id)
        WHERE p.feedtype_id = get_ldm_feedtype_id(%s)
        and r.valid > (now() - '24 hours'::interval))
    select distinct
    (select hostname from ldm_hostnames where id = p.relay_host_id) as relay,
    (select hostname from ldm_hostnames where id = p.node_host_id) as node
    from ldm_feedtype_paths p JOIN active a on (p.id = a.id)
    """,
        (feedtype,),
    )
    utcnow = datetime.datetime.utcnow()
    for row in cursor:
        upstreams.setdefault(row[1], []).append(row[0])

    if upstreams.get(hostname) is None:
        return json.dumps("NO_TOPOLOGY_ERROR")
    paths = [[hostname, x] for x in upstreams[hostname]]
    # print "inital upstreams are =>", paths
    depth = 2
    while depth < 10:
        newpaths = []
        for path in paths:
            if len(path) == depth:
                for up in upstreams.get(path[-1], []):
                    newpaths.append(path + [up])
        if len(newpaths) == 0:
            break
        paths = paths + newpaths
        # print("===== %s ====" % (depth,))
        # for path in paths:
        #    print(",".join(path))
        depth += 1
    res = dict()
    res["query_time[secs]"] = (utcnow - sts).total_seconds()
    res["hostname"] = hostname
    res["paths"] = paths
    return json.dumps(res)


def handle_feedtypes(hostname):
    """Generate geojson for this feedtype"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    sts = datetime.datetime.utcnow()
    cursor.execute(
        """
    select distinct f.feedtype from ldm_feedtypes f JOIN ldm_feedtype_paths p
    on (f.id = p.feedtype_id) WHERE p.node_host_id = get_ldm_host_id(%s)
    ORDER by f.feedtype
    """,
        (hostname,),
    )
    ets = datetime.datetime.utcnow()
    res = dict()
    res["query_time[secs]"] = (ets - sts).total_seconds()
    res["generation_time"] = ets.strftime("%Y-%m-%dT%H:%M:%SZ")
    res["hostname"] = hostname
    feedtypes = []
    for row in cursor:
        feedtypes.append(row[0])
    res["feedtypes"] = feedtypes
    return json.dumps(res)


def application(environ, start_response):
    """Answer request."""
    fields = parse_formvars(environ)
    cb = fields.get("callback", None)
    hostname = fields.get("hostname", "")
    service = fields.get("service", "")
    feedtype = fields.get("feedtype", "")
    since = fields.get("since")
    mckey = "/services/host/%s/%s.json?feedtype=%s" % (
        hostname,
        service,
        feedtype,
    )
    mc = memcache.Client(["localhost:11211"], debug=0)
    res = mc.get(mckey)
    if not res:
        if service == "feedtypes":
            res = handle_feedtypes(hostname)
        elif service == "rtstats":
            res = handle_rtstats(hostname, feedtype)
        elif service == "hourly":
            res = handle_hourly(hostname, feedtype, since)
        elif service == "daily":
            res = handle_daily(hostname, feedtype, since)
        elif service == "weekly":
            res = handle_weekly(hostname, feedtype, since)
        elif service == "topology":
            res = handle_topology(hostname, feedtype)
        mc.set(mckey, res, 3600)
    if cb is None:
        data = res
    else:
        data = "%s(%s)" % (cb, res)

    headers = [("Content-type", "application/json")]
    start_response("200 OK", headers)
    return [data.encode("ascii", "ignore")]
