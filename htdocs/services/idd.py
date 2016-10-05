#!/usr/bin/env python
"""Emit GeoJSON of IDD topology

    /services/idd.geojson

"""
import memcache
import cgi
import sys


def run(feedtype):
    """Generate geojson for this feedtype"""
    import psycopg2
    import json
    import datetime

    pgconn = psycopg2.connect(dbname='rtstats', user='nobody')
    cursor = pgconn.cursor()
    cursor.execute("""
    with data as (
        select r.feedtype_path, origin_hostname, relay_hostname, node_hostname,
        avg_latency, r.entry_added, p.feedtype,
        rank() OVER (PARTITION by r.feedtype_path ORDER by r.entry_added DESC)
        from ldm_rtstats r JOIN ldm_feedtype_paths p
            on (r.feedtype_path = p.id)
        WHERE r.entry_added > now() - '1 hour'::interval
        and p.feedtype = get_ldm_feedtype('HDS')),
    agg1 as (
        SELECT h.geom, h.hostname, d.feedtype_path, d.relay_hostname,
        d.avg_latency from ldm_hostnames h JOIN data d
            on (h.id = d.relay_hostname)
        WHERE rank = 1 and geom is not null and not ST_IsEmpty(geom)),
    agg2 as (
        SELECT h.geom, h.hostname, d.feedtype_path, d.node_hostname,
        d.avg_latency from ldm_hostnames h JOIN data d
            on (h.id = d.node_hostname)
        WHERE rank = 1 and geom is not null and not ST_IsEmpty(geom))

    SELECT st_asgeojson(st_makeline(o.geom, t.geom), 2),
    o.feedtype_path, o.relay_hostname,
    o.hostname, t.node_hostname, t.hostname, o.avg_latency,
    st_length(st_makeline(o.geom, t.geom))
    from agg1 o JOIN agg2 t on (o.feedtype_path = t.feedtype_path)
    """)
    utcnow = datetime.datetime.utcnow()
    res = {'type': 'FeatureCollection',
           'crs': {'type': 'EPSG',
                   'properties': {'code': 4326, 'coordinate_order': [1, 0]}},
           'features': [],
           'generation_time': utcnow.strftime("%Y-%m-%dT%H:%M:%SZ"),
           'count': cursor.rowcount}
    for row in cursor:
        if row[7] < 0.01:
            continue
        res['features'].append(dict(type="Feature",
                                    id=row[1],
                                    properties=dict(
                                        latency="%.2f" % (row[6],),
                                        relay=row[3],
                                        node=row[5]
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
    mckey = "/services/idd.geojson|%s" % (feedtype,)
    mc = memcache.Client(['memcached.local:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = run(feedtype)
        mc.set(mckey, res, 60)
    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))

if __name__ == '__main__':
    main()
