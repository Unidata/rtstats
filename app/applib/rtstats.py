from twisted.python import log
import pytz
import datetime


def split_origin(val):
    """Convert a rtstats origin string into two parts

    Args:
      val (string): the string formated like <host>_v_<host>
    Returns:
      list: (origin_hostname, relay_hostname)
    """
    tokens = val.split("_v_")
    if len(tokens) != 2:
        log.msg("split_origin provided invalid string: %s" % (repr(val),))
        return [None, None]
    a, b = tokens
    if b == "":
        b = a
    return [a, b]


def s2ts(timestamp):
    """Convert a string timestamp to datetime object

    Args:
      timestamp (string): string in the form of YYYYMMDDHHMI

    Returns:
      datetime: with tzinfo set to UTC
    """
    ts = datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S')
    return ts.replace(tzinfo=pytz.utc)


def parser(cursor, raw):
    """Parse and save rtstats content

    Args:
      cursor: database cursor
      raw (string): content of the rtstats report
    """
    tokens = raw.strip().split()
    if len(tokens) != 11:
        log.msg("parser did not find 11 tokens in %s" % (repr(raw),))
        return
    # This 99% likely to be a truncated path due to old rtstats bug
    # we really can only ignore these for now.
    if len(tokens[4]) == 32:
        return
    (origin_hostname, relay_hostname) = split_origin(tokens[4])
    # this is likely from the old case of bug with rtstats
    if origin_hostname is None:
        return
    queue_arrival = s2ts(tokens[0])
    queue_recent = s2ts(tokens[1])
    nprods = tokens[5]
    nbytes = tokens[6]
    avg_latency = tokens[7]
    max_latency = tokens[8]
    slowest_at = tokens[9]
    version = tokens[10]
    feedtype = tokens[3]
    node_hostname = tokens[2]

    cursor.execute("""INSERT into ldm_rtstats
    (feedtype_path, queue_arrival, queue_recent, nprods, nbytes,
    avg_latency, max_latency, slowest_at, version) VALUES
    (get_ldm_feedtype_path(get_ldm_feedtype(%s),
        get_ldm_hostname(%s), get_ldm_hostname(%s),
        get_ldm_hostname(%s)), %s, %s, %s, %s,
    %s, %s, %s, get_ldm_version(%s))
    """, (feedtype, origin_hostname, relay_hostname, node_hostname,
          queue_arrival,  queue_recent, nprods, nbytes, avg_latency,
          max_latency, slowest_at, version))
