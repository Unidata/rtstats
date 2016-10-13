#!/usr/bin/env python
"""Emit JSON of feedtypes

    /services/feedtypes.json

"""
import memcache
import cgi
import sys
import rtstats_util as util


def run():
    """Generate geojson for this feedtype"""
    import json
    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    cursor.execute("""
    SELECT feedtype from ldm_feedtypes ORDER by feedtype
    """)
    res = dict(feedtypes=[])
    for row in cursor:
        res['feedtypes'].append(row[0])

    return json.dumps(res)


def main():
    """Go Main Go"""
    sys.stdout.write("Content-type: application/json\n\n")
    form = cgi.FieldStorage()
    cb = form.getfirst('callback', None)
    mckey = "/services/feedtypes.json"
    mc = memcache.Client(['memcached.local:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = run()
        mc.set(mckey, res, 86400)
    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))

if __name__ == '__main__':
    main()
