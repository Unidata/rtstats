#!/usr/bin/env python
"""Emit JSON of feedtype

/services/feedtype/<feedtype>/topology.json

"""

import datetime
import json

import memcache
import rtstats_util as util
from paste.request import parse_formvars


def handle_topology(feedtype, reverse=False):
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
    ets = datetime.datetime.utcnow()
    for row in cursor:
        if reverse:
            upstreams.setdefault(row[0], []).append(row[1])
        else:
            upstreams.setdefault(row[1], []).append(row[0])

    res = dict()
    res["query_time[secs]"] = (ets - sts).total_seconds()
    res["generation_time"] = ets.strftime("%Y-%m-%dT%H:%M:%SZ")
    res["feedtype"] = feedtype
    res["upstreams" if not reverse else "downstreams"] = upstreams
    return json.dumps(res)


def application(environ, start_response):
    """Answer request."""
    fields = parse_formvars(environ)
    cb = fields.get("callback", None)
    feedtype = fields.get("feedtype", "")
    service = fields.get("service", "")
    mckey = "/services/feedtype/%s/%s.json" % (feedtype, service)
    mc = memcache.Client(["localhost:11211"], debug=0)
    res = mc.get(mckey)
    if not res:
        if service == "topology":
            res = handle_topology(feedtype)
        elif service == "rtopology":
            res = handle_topology(feedtype, True)
        mc.set(mckey, res, 3600)
    if cb is None:
        data = res
    else:
        data = "%s(%s)" % (cb, res)

    headers = [("Content-type", "application/json")]
    start_response("200 OK", headers)
    return [data.encode("ascii", "ignore")]
