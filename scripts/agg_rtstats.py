"""Aggregate the hourly rtstats"""
import rtstats_util as util
import datetime

def daily():
    pgconn = util.get_dbconn(rw=True)
    cursor = pgconn.cursor()
    # we run for the day for the previous hour
    utcnow = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    utcnow = utcnow.replace(tzinfo=pytz.utc)
    sts = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)
    ets = sts + datetime.timedelta(hours=24)
    cursor.execute("""
        DELETE from ldm_rtstats_daily WHERE valid = %s
        """, (sts.date(),))
    cursor.execute("""
    WITH agg as (
        select feedtype_path_id, %s as v,
        count(*), sum(nprods), sum(nbytes),
        min(avg_latency), avg(avg_latency), max(max_latency) from ldm_rtstats
        WHERE entry_added >= %s
        and entry_added < %s
        GROUP by feedtype_path_id, v)
    INSERT into ldm_rtstats_daily SELECT * from agg
    """, (sts.date(), sts, ets))
    cursor.close()
    pgconn.commit()
    pgconn.close()


def hourly():
    pgconn = util.get_dbconn(rw=True)
    cursor = pgconn.cursor()
    # figure out what our most recent stats are for
    cursor.execute("""SELECT max(valid) from ldm_rtstats_hourly""")
    maxval = cursor.fetchone()[0]
    cursor.execute("""
    WITH agg as (
        select feedtype_path_id, date_trunc('hour', entry_added) as v,
        count(*), sum(nprods), sum(nbytes),
        min(avg_latency), avg(avg_latency), max(max_latency) from ldm_rtstats
        WHERE entry_added >= %s + '1 hour'::interval
        and entry_added < date_trunc('hour', now())
        GROUP by feedtype_path_id, v)
    INSERT into ldm_rtstats_hourly SELECT * from agg
    """, (maxval or datetime.datetime(1971, 1, 1), ))
    cursor.close()
    pgconn.commit()
    pgconn.close()

if __name__ == '__main__':
    daily()
    hourly()
