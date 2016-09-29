---------------------------
-- Storage of LDM version strings

CREATE TABLE ldm_versions(
	id SERIAL UNIQUE NOT NULL,
	version varchar(32),
	entry_added timestamptz default now());
GRANT SELECT on ldm_versions to nobody;

---------------------------
-- Storage of LDM feedtypes

CREATE TABLE ldm_feedtypes(
	id SERIAL UNIQUE NOT NULL,
	feedtype varchar(32) UNIQUE NOT NULL,
	entry_added timestamptz default now());
GRANT SELECT on ldm_feedtypes to nobody;

---------------------------------------
-- Storage of hostnames reported by LDM
--   Note: These may or may not be FQDNs, IPs or even valid

CREATE TABLE ldm_hostnames(
	id SERIAL UNIQUE NOT NULL,
	hostname varchar(256) UNIQUE NOT NULL
		CONSTRAINT notblank_hostname CHECK (hostname != ''),
	entry_added timestamptz default now()
);
GRANT SELECT on ldm_hostnames to nobody;

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

--------------------------------
-- Storage of actual rtstats!

CREATE TABLE ldm_rtstats(
	feedtype_path int REFERENCES ldm_feedtype_paths(id),
	queue_arrival timestamptz,
	queue_recent timestamptz,
	nprods int,
	nbytes int,
	avg_latency real,
	max_latency real,
	slowest_at varchar(9),
	version int REFERENCES ldm_versions(id),
	entry_added timestamptz default now()
);
GRANT SELECT on ldm_rtstats to nobody;

	