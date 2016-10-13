"""Collection of Utilities for rtstats"""

import psycopg2
import json
import os


def get_config():
    """Return a dict() of our runtime configuration"""
    fn = "%s/settings.json" % (os.path.join(os.path.dirname(__file__),
                                            "../config"),)
    return json.load(open(fn))


def get_dbconn(rw=False):
    """return a database connection"""
    config = get_config()
    dbopts = config['databaserw' if rw is True else 'databasero']

    return psycopg2.connect(dbname=dbopts['name'], host=dbopts['host'],
                            user=dbopts['user'], password=dbopts['password'])
