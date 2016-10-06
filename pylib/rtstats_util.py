"""Collection of Utilities for rtstats"""

import psycopg2


def get_dbconn():
    """return a database connection"""
    return psycopg2.connect(dbname='rtstats', host='localhost')
