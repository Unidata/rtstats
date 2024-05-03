"""Aggregate the hourly rtstats"""

import datetime

import pytz
import rtstats_util as util


def daily(pgconn):
    """Daily workflow"""
    cursor = pgconn.cursor()
    # we run for the day for the previous hour
    utcnow = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    utcnow = utcnow.replace(tzinfo=pytz.utc)
    sts = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)
    ets = sts + datetime.timedelta(hours=24)
    cursor.execute(
        """
        DELETE from ldm_rtstats_daily WHERE valid = %s
        """,
        (sts.date(),),
    )
    cursor.execute(
        """
    with agg as (
        SELECT feedtype_path_id, %s as v, sum(entries), sum(nprods),
        sum(nbytes), min(min_latency), avg(avg_latency),
        max(max_latency), max(version_id) from ldm_rtstats_hourly
        where valid >= %s and valid < %s
        GROUP by feedtype_path_id)
    INSERT into ldm_rtstats_daily SELECT * from agg
    """,
        (sts.date(), sts, ets),
    )
    cursor.close()
    pgconn.commit()


def hourly(pgconn):
    """Hourly Workflow"""
    cursor = pgconn.cursor()
    # figure out what our most recent stats are for
    cursor.execute("""SELECT max(valid) from ldm_rtstats_hourly""")
    maxval = cursor.fetchone()[0]
    # Do non-NEXRAD2 first, as we need not optimize this one
    cursor.execute(
        """
    WITH agg as (
        select feedtype_path_id, date_trunc('hour', queue_arrival) as v,
        count(*), max(nprods), max(nbytes),
        min(avg_latency), avg(avg_latency), max(max_latency),
        max(version_id) as version_id
        from ldm_rtstats r JOIN ldm_feedtype_paths p
            on (r.feedtype_path_id = p.id)
        WHERE queue_arrival >= %s + '1 hour'::interval
        and queue_arrival < date_trunc('hour', now())
        and p.feedtype_id != get_ldm_feedtype_id('NEXRAD2')
        GROUP by feedtype_path_id, v)
    INSERT into ldm_rtstats_hourly SELECT * from agg
    """,
        (maxval or datetime.datetime(1971, 1, 1),),
    )
    cursor.close()
    pgconn.commit()

    # Do NEXRAD2 now with some optimizations
    #  + we basically group by relay + node and then set the origin to
    #    the relay node
    cursor = pgconn.cursor()
    cursor.execute(
        """
    WITH agg as (
        select date_trunc('hour', queue_arrival) as v,
        count(*), max(nprods) as max_nprods, max(nbytes) as max_nbytes,
        min(avg_latency) as min_latency,
        avg(avg_latency) as avg_latency,
        max(max_latency) as max_latency,
        p.origin_host_id, p.relay_host_id, p.node_host_id,
        max(version_id) as version_id
        from ldm_rtstats r JOIN ldm_feedtype_paths p
            on (r.feedtype_path_id = p.id)
        WHERE queue_arrival >= %s + '1 hour'::interval
        and queue_arrival < date_trunc('hour', now())
        and p.feedtype_id = get_ldm_feedtype_id('NEXRAD2')
        GROUP by origin_host_id, relay_host_id, node_host_id, v),
    agg2 as (
        SELECT relay_host_id, node_host_id, v, sum(count) as count,
        sum(max_nprods) as nprods, sum(max_nbytes) as nbytes,
        min(min_latency) as min_latency, avg(avg_latency) as avg_latency,
        max(max_latency) as max_latency, max(version_id) as version_id
        from agg
        GROUP By relay_host_id, node_host_id, v)
    INSERT into ldm_rtstats_hourly(feedtype_path_id, valid, entries,
    nprods, nbytes, min_latency, avg_latency, max_latency, version_id)
        SELECT get_ldm_feedtype_path_id(get_ldm_feedtype_id('NEXRAD2'),
        relay_host_id, relay_host_id,  node_host_id), v, count,
        nprods, nbytes, min_latency, avg_latency, max_latency,
        version_id from agg2
    """,
        (maxval or datetime.datetime(1971, 1, 1),),
    )
    cursor.close()
    pgconn.commit()


def cleanup(pgconn):
    """Based on configuration, purge old data within the database"""
    cursor = pgconn.cursor()
    config = util.get_config()
    for table, prop in zip(
        ["ldm_rtstats", "ldm_rtstats_hourly", "ldm_rtstats_daily"],
        [
            "retain_rtstats_raw[hours]",
            "retain_rtstats_hourly[days]",
            "retain_rtstats_daily[days]",
        ],
    ):
        interval = config.get(prop)
        if interval is None or interval <= 0:
            continue
        timecol = "entry_added" if table == "ldm_rtstats" else "valid"
        multiplier = 24 if table != "ldm_rtstats" else 1
        hours = interval * multiplier
        cursor.execute(
            """
        DELETE from """
            + table
            + """
        WHERE """
            + timecol
            + """ < (now() - '%s hours'::interval)
        """
            % (hours,)
        )
        # print("Removed %s rows from table: %s" % (cursor.rowcount, table))
    cursor.close()
    pgconn.commit()


def main():
    """Our workflow"""
    pgconn = util.get_dbconn(rw=True)
    hourly(pgconn)
    daily(pgconn)
    cleanup(pgconn)


if __name__ == "__main__":
    main()
