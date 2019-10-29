"""Use GeoIP and assign lat/lon to hostnames"""
from __future__ import print_function
import os
import json
import re
import socket

import psycopg2
import pygeoip

RE_IP = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def get_dbconn():
    fn = "%s/settings.json" % (
        os.path.join(os.path.dirname(__file__), "../config"),
    )
    config = json.load(open(fn))
    dbopt = config["databaserw"]
    return psycopg2.connect(
        host=dbopt["host"],
        user=dbopt["user"],
        password=dbopt["password"],
        dbname=dbopt["name"],
    )


def main():
    pgconn = get_dbconn()
    cursor = pgconn.cursor()
    cursor2 = pgconn.cursor()
    fn = "/usr/share/GeoIP/GeoLiteCity.dat"
    if os.path.isfile("/tmp/GeoLiteCity.dat"):
        fn = "/tmp/GeoLiteCity.dat"
        print("assign_hostname_geom.py found local db %s" % (fn,))
    gi = pygeoip.GeoIP(fn)

    cursor.execute(
        """
        SELECT id, hostname from ldm_hostnames
        WHERE geom is null
    """
    )
    for row in cursor:
        if RE_IP.match(row[1]):
            gir = gi.record_by_addr(row[1])
        else:
            try:
                gir = gi.record_by_name(row[1])
            except socket.gaierror:
                gir = None
        if gir is not None:
            cursor2.execute(
                """UPDATE ldm_hostnames
            SET geom = 'SRID=4326;POINT(%s %s)' where id = %s
            """,
                (gir["longitude"], gir["latitude"], row[0]),
            )
        else:
            cursor2.execute(
                """UPDATE ldm_hostnames
            SET geom = 'SRID=4326;POINT EMPTY' where id = %s
            """,
                (row[0],),
            )

    cursor2.close()
    pgconn.commit()
    pgconn.close()


if __name__ == "__main__":
    main()
