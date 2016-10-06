#!/usr/bin/env python
"""Emit JSON of host

    /services/host/<hostname>/feedtypes.json

"""
import memcache
import cgi
import sys
import rtstats_util as util


def handle_feedtypes(hostname):
    """Generate geojson for this feedtype"""
    import json

    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    cursor.execute("""
    select distinct f.feedtype from ldm_feedtypes f JOIN ldm_feedtype_paths p
    on (f.id = p.feedtype_id) WHERE p.node_host_id = get_ldm_host_id(%s)
    ORDER by f.feedtype
    """, (hostname, ))
    res = dict()
    res['hostname'] = hostname
    feedtypes = []
    for row in cursor:
        feedtypes.append(row[0])
    res['feedtypes'] = feedtypes
    return json.dumps(res)


def main():
    """Go Main Go"""
    sys.stdout.write("Content-type: application/json\n\n")
    form = cgi.FieldStorage()
    cb = form.getfirst('callback', None)
    hostname = form.getfirst('hostname', '')
    service = form.getfirst('service', '')
    mckey = "/services/host/%s/%s.json" % (hostname, service)
    mc = memcache.Client(['memcached.local:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        if service == 'feedtypes':
            res = handle_feedtypes(hostname)
        mc.set(mckey, res, 3600)
    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))

if __name__ == '__main__':
    main()
