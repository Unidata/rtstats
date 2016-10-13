CREATE EXTENSION postgis;

---------------------------
-- Storage of LDM version strings

CREATE TABLE ldm_versions(
	id SERIAL UNIQUE NOT NULL,
	version varchar(32),
	entry_added timestamptz default now());
GRANT SELECT on ldm_versions to nobody;
GRANT ALL on ldm_versions to ldm;
GRANT ALL on ldm_versions_id_seq to ldm;

-- lookup or creation of ldm_versions
CREATE OR REPLACE FUNCTION get_ldm_version_id(_version text,
	OUT ldm_version_id int) AS
$func$
BEGIN

LOOP
   BEGIN  -- start inner block inside loop to handle possible exception

   SELECT INTO ldm_version_id f.id FROM ldm_versions f
   WHERE f.version = _version;

   IF NOT FOUND THEN
      INSERT INTO ldm_versions(version) VALUES (_version)
      RETURNING ldm_versions.id INTO ldm_version_id;
   END IF;

   EXCEPTION WHEN UNIQUE_VIOLATION THEN     -- inserted in concurrent session.
      RAISE NOTICE 'It actually happened!'; -- hardly ever happens
   END;

   EXIT WHEN ldm_version_id IS NOT NULL;          -- else keep looping
END LOOP;

END
$func$ LANGUAGE plpgsql;

---------------------------
-- Storage of LDM feedtypes

CREATE TABLE ldm_feedtypes(
	id SERIAL UNIQUE NOT NULL,
	feedtype varchar(32) UNIQUE NOT NULL,
	entry_added timestamptz default now());
GRANT SELECT on ldm_feedtypes to nobody;
GRANT ALL on ldm_feedtypes to ldm;
GRANT ALL on ldm_feedtypes_id_seq to ldm;

-- lookup or creation of ldm_feedtypes
CREATE OR REPLACE FUNCTION get_ldm_feedtype_id(_feedtype text,
	OUT ldm_feedtype_id int) AS
$func$
BEGIN

LOOP
   BEGIN  -- start inner block inside loop to handle possible exception

   SELECT INTO ldm_feedtype_id f.id FROM ldm_feedtypes f
   WHERE f.feedtype = _feedtype;

   IF NOT FOUND THEN
      INSERT INTO ldm_feedtypes(feedtype) VALUES (_feedtype)
      RETURNING ldm_feedtypes.id INTO ldm_feedtype_id;
   END IF;

   EXCEPTION WHEN UNIQUE_VIOLATION THEN     -- inserted in concurrent session.
      RAISE NOTICE 'It actually happened!'; -- hardly ever happens
   END;

   EXIT WHEN ldm_feedtype_id IS NOT NULL;          -- else keep looping
END LOOP;

END
$func$ LANGUAGE plpgsql;

---------------------------------------
-- Storage of hostnames reported by LDM
--   Note: These may or may not be FQDNs, IPs or even valid

CREATE TABLE ldm_hostnames(
	id SERIAL UNIQUE NOT NULL,
	hostname varchar(256) UNIQUE NOT NULL
		CONSTRAINT notblank_hostname CHECK (hostname != ''),
	geom geometry(POINT, 4326),
	entry_added timestamptz default now()
);
GRANT SELECT on ldm_hostnames to nobody;
CREATE INDEX ldm_hostnames_hostname_idx on ldm_hostnames(hostname);
GRANT ALL on ldm_hostnames to ldm;
GRANT ALL on ldm_hostnames_id_seq to ldm;

-- lookup or creation of ldm_hostnames
CREATE OR REPLACE FUNCTION get_ldm_host_id(_hostname text,
	OUT ldm_hostname_id int) AS
$func$
BEGIN

LOOP
   BEGIN  -- start inner block inside loop to handle possible exception

   SELECT INTO ldm_hostname_id f.id FROM ldm_hostnames f
   WHERE f.hostname = lower(_hostname);

   IF NOT FOUND THEN
      INSERT INTO ldm_hostnames(hostname) VALUES (lower(_hostname))
      RETURNING ldm_hostnames.id INTO ldm_hostname_id;
   END IF;

   EXCEPTION WHEN UNIQUE_VIOLATION THEN     -- inserted in concurrent session.
      RAISE NOTICE 'It actually happened!'; -- hardly ever happens
   END;

   EXIT WHEN ldm_hostname_id IS NOT NULL;          -- else keep looping
END LOOP;

END
$func$ LANGUAGE plpgsql;

--------------------------------
-- Storage of LDM feedtype paths

CREATE TABLE ldm_feedtype_paths(
	id SERIAL UNIQUE NOT NULL,
	feedtype_id int REFERENCES ldm_feedtypes(id),
	origin_host_id int REFERENCES ldm_hostnames(id),
	relay_host_id int REFERENCES ldm_hostnames(id),
	node_host_id int REFERENCES ldm_hostnames(id),
	entry_added timestamptz default now()
);
GRANT SELECT on ldm_feedtype_paths to nobody;
CREATE INDEX ldm_feedtype_paths_idx on
	ldm_feedtype_paths(feedtype_id, origin_host_id, relay_host_id, node_host_id);
GRANT ALL on ldm_feedtype_paths to ldm;
GRANT ALL on ldm_feedtype_paths_id_seq to ldm;

-- lookup or creation of ldm_feedtype_paths
CREATE OR REPLACE FUNCTION get_ldm_feedtype_path_id(_feedtype int, _origin int,
    _relay int, _node int, OUT feedtype_path_id int) AS
$func$
BEGIN

LOOP
   BEGIN  -- start inner block inside loop to handle possible exception

   SELECT INTO feedtype_path_id f.id FROM ldm_feedtype_paths f
   WHERE f.feedtype_id = _feedtype and
         f.origin_host_id = _origin and
         f.relay_host_id = _relay and
         f.node_host_id = _node;

   IF NOT FOUND THEN
      INSERT INTO ldm_feedtype_paths(feedtype_id, origin_host_id,
      relay_host_id, node_host_id) VALUES (
	  _feedtype, _origin,
	  _relay, _node)
      RETURNING ldm_feedtype_paths.id INTO feedtype_path_id;
   END IF;

   EXCEPTION WHEN UNIQUE_VIOLATION THEN     -- inserted in concurrent session.
      RAISE NOTICE 'It actually happened!'; -- hardly ever happens
   END;

   EXIT WHEN feedtype_path_id IS NOT NULL;          -- else keep looping
END LOOP;

END
$func$ LANGUAGE plpgsql;

--------------------------------
-- Storage of actual rtstats!

CREATE TABLE ldm_rtstats(
	feedtype_path_id int REFERENCES ldm_feedtype_paths(id),
	queue_arrival timestamptz,
	queue_recent timestamptz,
	nprods bigint,
	nbytes bigint,
	avg_latency real,
	max_latency real,
	slowest_at varchar(32),
	version_id int REFERENCES ldm_versions(id),
	entry_added timestamptz default now()
);
GRANT SELECT on ldm_rtstats to nobody;
GRANT ALL on ldm_rtstats to ldm;
CREATE INDEX ldm_rtstats_queue_arrival_idx
	ON ldm_rtstats(queue_arrival);

--------------------------------------------------------------------
-- Storage of hourly aggregated stats
--   + these are populated each hour via a cron job
CREATE TABLE ldm_rtstats_hourly(
	feedtype_path_id int REFERENCES ldm_feedtype_paths(id),
	valid timestamptz,
	entries int,
	nprods bigint,
	nbytes bigint,
	min_latency real,
	avg_latency real,
	max_latency real
);
GRANT SELECT on ldm_rtstats_hourly to nobody;
GRANT ALL on ldm_rtstats_hourly to ldm;
CREATE INDEX ldm_rstats_hourly_idx
	on ldm_rtstats_hourly(feedtype_path_id, valid);

----------------------------------------------------------------------
-- Storage of daily aggregated stats
--   + these are populated via a cron job
CREATE TABLE ldm_rtstats_daily(
	feedtype_path_id int REFERENCES ldm_feedtype_paths(id),
	valid date,
	entries int,
	nprods bigint,
	nbytes bigint,
	min_latency real,
	avg_latency real,
	max_latency real
);
GRANT SELECT on ldm_rtstats_daily to nobody;
GRANT ALL on ldm_rtstats_daily to ldm;
CREATE INDEX ldm_rstats_daily_idx
	on ldm_rtstats_daily(feedtype_path_id, valid);
