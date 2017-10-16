"""Collection of Utilities for rtstats"""

import json
import os
os.environ['MPLCONFIGDIR'] = "/tmp"  # hack

import psycopg2
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
    xlim = ax.get_xlim()
    days = xlim[1] - xlim[0]

    daily = True
    if days < 4:
        daily = False
        ax.xaxis.set_major_locator(mdates.HourLocator(range(0, 24, 4)))
    elif days < 31:
        ax.xaxis.set_major_locator(mdates.DayLocator([1, 8, 15, 22, 29]))
    elif days < 63:
        ax.xaxis.set_major_locator(mdates.DayLocator([1, 15]))
    else:
        ax.xaxis.set_major_locator(mdates.DayLocator([1, ]))

    def my_formatter(x, pos=None):
        x = mdates.num2date(x)
        if daily:
            fmt = "%-d %b"
        elif pos == 0 or x.hour == 0:
            fmt = "%-Hz\n%-d %b"
        else:
            fmt = "%-H"
        return x.strftime(fmt)

    ax.xaxis.set_major_formatter(FuncFormatter(my_formatter))
