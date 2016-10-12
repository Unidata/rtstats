#!/usr/bin/env python
"""Emit JSON of host

    /services/host/<hostname>/feedtypes.json
    /services/host/<hostname>/rtstats.json

"""
import memcache
import cgi
import sys
import rtstats_util as util


def handle_rtstats(hostname, feedtype):
    """Emit JSON for rtstats for this host"""
    import json

    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    flimit = ''
    if feedtype != '':
        flimit = " and p.feedtype_id = get_ldm_feedtype_id('%s') " % (feedtype,
                                                                      )
    cursor.execute("""
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
    r.entry_added > now() - '36 hours'::interval """ + flimit + """
    ORDER by r.entry_added ASC
    """, (hostname, ))
    res = dict()
    res['hostname'] = hostname
    res['columns'] = ['entry_added', 'feedtype_path_id', 'origin', 'relay',
                      'avg_latency', 'feedtype']
    res['data'] = []
    for row in cursor:
        res['data'].append(row)
    return json.dumps(res)


def handle_hourly(hostname, feedtype):
    """Emit JSON for rtstats for this host"""
    import json

    pgconn = util.get_dbconn()
    cursor = pgconn.cursor()
    flimit = ''
    if feedtype != '':
        flimit = " and p.feedtype_id = get_ldm_feedtype_id('%s') " % (feedtype,
                                                                      )
    cursor.execute("""
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
    p.node_host_id = get_ldm_host_id(%s) and
    h.valid > now() - '36 hours'::interval """ + flimit + """
    ORDER by h.valid ASC
    """, (hostname, ))
    res = dict()
    res['hostname'] = hostname
    res['columns'] = ['valid', 'feedtype_path_id', 'origin', 'relay',
                      'min_latency', 'avg_latency', 'max_latency',
                      'nprods', 'nbytes', 'feedtype']
    res['data'] = []
    for row in cursor:
        res['data'].append(row)
    return json.dumps(res)


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
    feedtype = form.getfirst('feedtype', '')
    mckey = "/services/host/%s/%s.json?feedtype=%s" % (hostname, service,
                                                       feedtype)
    mc = memcache.Client(['memcached.local:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        if service == 'feedtypes':
            res = handle_feedtypes(hostname)
        elif service == 'rtstats':
            res = handle_rtstats(hostname, feedtype)
        elif service == 'hourly':
            res = handle_hourly(hostname, feedtype)
        mc.set(mckey, res, 3600)
    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))

if __name__ == '__main__':
    main()
