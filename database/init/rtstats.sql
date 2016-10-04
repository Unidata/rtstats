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
CREATE OR REPLACE FUNCTION get_ldm_version(_version text,
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
CREATE OR REPLACE FUNCTION get_ldm_feedtype(_feedtype text,
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
CREATE OR REPLACE FUNCTION get_ldm_hostname(_hostname text,
	OUT ldm_hostname_id int) AS
$func$
BEGIN

LOOP
   BEGIN  -- start inner block inside loop to handle possible exception

   SELECT INTO ldm_hostname_id f.id FROM ldm_hostnames f
   WHERE f.hostname = _hostname;

   IF NOT FOUND THEN
      INSERT INTO ldm_hostnames(hostname) VALUES (_hostname)
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
	feedtype int REFERENCES ldm_feedtypes(id),
	origin_hostname int REFERENCES ldm_hostnames(id),
	relay_hostname int REFERENCES ldm_hostnames(id),
	node_hostname int REFERENCES ldm_hostnames(id),
	entry_added timestamptz default now()
);
GRANT SELECT on ldm_feedtype_paths to nobody;
CREATE INDEX ldm_feedtype_paths_idx on
	ldm_feedtype_paths(feedtype, origin_hostname, relay_hostname,
	node_hostname);
GRANT ALL on ldm_feedtype_paths to ldm;
GRANT ALL on ldm_feedtype_paths_id_seq to ldm;

-- lookup or creation of ldm_feedtype_paths
CREATE OR REPLACE FUNCTION get_ldm_feedtype_path(_feedtype int, _origin int,
    _relay int, _node int, OUT feedtype_path_id int) AS
$func$
BEGIN

LOOP
   BEGIN  -- start inner block inside loop to handle possible exception

   SELECT INTO feedtype_path_id f.id FROM ldm_feedtype_paths f
   WHERE f.feedtype = _feedtype and
         f.origin_hostname = _origin and
         f.relay_hostname = _relay and
         f.node_hostname = _node;

   IF NOT FOUND THEN
      INSERT INTO ldm_feedtype_paths(feedtype, origin_hostname,
      relay_hostname, node_hostname) VALUES (
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
	feedtype_path int REFERENCES ldm_feedtype_paths(id),
	queue_arrival timestamptz,
	queue_recent timestamptz,
	nprods bigint,
	nbytes bigint,
	avg_latency real,
	max_latency real,
	slowest_at varchar(32),
	version int REFERENCES ldm_versions(id),
	entry_added timestamptz default now()
);
GRANT SELECT on ldm_rtstats to nobody;
GRANT ALL on ldm_rtstats to ldm;

