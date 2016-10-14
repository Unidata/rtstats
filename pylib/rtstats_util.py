"""Collection of Utilities for rtstats"""

import psycopg2
import json
import os
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter


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


def fancy_labels(ax):
    """Make matplotlib date axis labels great again"""
    def my_formatter(x, pos=None):
        x = mdates.num2date(x)
        if pos == 0 or x.hour == 0:
            fmt = "%-Hz\n%-d %b"
        else:
            fmt = "%-H"
        return x.strftime(fmt)

    ax.xaxis.set_major_locator(mdates.HourLocator(range(0, 24, 4)))
    ax.xaxis.set_major_formatter(FuncFormatter(my_formatter))
