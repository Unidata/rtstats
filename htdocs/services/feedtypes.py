#!/usr/bin/env python
"""Emit JSON of feedtypes

    /services/feedtypes.json

"""
import json

import memcache
from paste.request import parse_formvars
import rtstats_util as util


def run():
    """Generate geojson for this feedtype"""
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    cursor.execute(
        """
    SELECT feedtype from ldm_feedtypes ORDER by feedtype
    """
    )
    res = dict(feedtypes=[])
    for row in cursor:
        res["feedtypes"].append(row[0])

    return json.dumps(res)


def application(environ, start_response):
    """Answer request."""
    fields = parse_formvars(environ)
    cb = fields.get("callback", None)
    mckey = "/services/feedtypes.json"
    mc = memcache.Client(["localhost:11211"], debug=0)
    res = mc.get(mckey)
    if not res:
        res = run()
        mc.set(mckey, res, 86400)
    if cb is None:
        data = res
    else:
        data = "%s(%s)" % (cb, res)

    headers = [("Content-type", "application/json")]
    start_response("200 OK", headers)
    return [data.encode("ascii")]
