"""Use GeoIP and assign lat/lon to hostnames"""

from __future__ import print_function

import json
import os
import re
import socket

import geoip2.database
import psycopg2

RE_IP = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def get_dbconn():
    """Get database."""
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
    """Go Main Go."""
    pgconn = get_dbconn()
    cursor = pgconn.cursor()
    cursor2 = pgconn.cursor()
    fn = "/opt/rtstats/GeoLite2-City/GeoLite2-City.mmdb"
    reader = geoip2.database.Reader(fn)

    cursor.execute(
        """
        SELECT id, hostname from ldm_hostnames
        WHERE geom is null
    """
    )
    for row in cursor:
        if RE_IP.match(row[1]):
            try:
                response = reader.city(row[1])
            except Exception:
                response = None
        else:
            try:
                response = reader.city(socket.gethostbyname(row[1]))
            except Exception:
                response = None
        if response is not None:
            cursor2.execute(
                """UPDATE ldm_hostnames
            SET geom = 'SRID=4326;POINT(%s %s)' where id = %s
            """,
                (
                    response.location.longitude,
                    response.location.latitude,
                    row[0],
                ),
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
