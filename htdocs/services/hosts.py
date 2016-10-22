#!/usr/bin/env python
"""Emit JSON of hosts

    /services/hosts.geojson

This service caches for 1 hour before refreshing.
"""
import memcache
import cgi
import sys


def run():
    """Generate geojson for this feedtype"""
    import psycopg2
    import json
    import datetime

    pgconn = psycopg2.connect(dbname='rtstats', user='nobody')
    cursor = pgconn.cursor()
    sts = datetime.datetime.utcnow()
    cursor.execute("""
    WITH data as (
        SELECT distinct feedtype_path_id, version_id from ldm_rtstats_hourly
        WHERE valid > now() - '24 hours'::interval),
    agg1 as (
        SELECT distinct p.node_host_id, d.version_id from
        data d JOIN ldm_feedtype_paths p on (d.feedtype_path_id = p.id))
    SELECT ST_asGeoJson(h.geom, 2), h.hostname, v.version
    from agg1 a1, ldm_versions v, ldm_hostnames h
    WHERE a1.node_host_id = h.id and v.id = a1.version_id
    and h.geom is not null
    ORDER by hostname ASC
    """)
    utcnow = datetime.datetime.utcnow()
    res = {'type': 'FeatureCollection',
           'crs': {'type': 'EPSG',
                   'properties': {'code': 4326, 'coordinate_order': [1, 0]}},
           'features': [],
           'query_time[secs]': (utcnow - sts).total_seconds(),
           'generation_time': utcnow.strftime("%Y-%m-%dT%H:%M:%SZ"),
           'count': cursor.rowcount}
    for row in cursor:
        res['features'].append(dict(type="Feature",
                                    id=row[1],
                                    properties=dict(
                                        hostname=row[1],
                                        ldmversion=row[2]
                                        ),
                                    geometry=json.loads(row[0])
                                    ))

    return json.dumps(res)


def main():
    """Go Main Go"""
    sys.stdout.write("Content-type: application/vnd.geo+json\n\n")
    form = cgi.FieldStorage()
    cb = form.getfirst('callback', None)
    mckey = "/services/hosts.geojson"
    mc = memcache.Client(['memcached.local:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = run()
        mc.set(mckey, res, 3600)
    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))

if __name__ == '__main__':
    main()
