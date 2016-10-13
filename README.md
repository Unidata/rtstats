# rtstats
Unidata rtstats revamp, see discussion at @Unidata/unidata-usercomm#2 

[![Build Status](https://travis-ci.org/akrherz/rtstats.svg)](https://travis-ci.org/akrherz/rtstats)

### Warning

The database schema is not finalized yet as I do some initial iteration.  Once
finalized, I'll support an upgrade path via the `database/schema_manager.py`
tool.

### Installation

This software makes the following assumptions.

1. RHEL/centos 7.2 64bit server, subscribed to EPEL and PGRPMS 9.6 yum repos
2. selinux is not enabled
3. this repository is checked out to `/opt/rtstats`
4. LDM is installed and setup to receive rtstats

This software has three primary components that can be run on a single VM or
spread over three instances.

1. LDM ingest script, which parses rtstats and mines into a database
2. A database that stores the information
3. A website with tools and web services that provide users access to the database
and queries backend HTTP services provided by LDM ingest process

rpm -ivh https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-redhat96-9.6-3.noarch.rpm
yum -y install git postgresql96-server httpd php mod_ssl \
libxml2-devel gcc-c++ byacc make perl bc lftp python-twisted-web \
pytz python-psycopg2 python-GeoIP postgis2_96 memcached python-requests \
python-pandas

add rtstats.local to /etc/hosts

### `config/settings.json` options

Various codes within this repository get their runtime configuration from
the `config/settings.json` file.  The following table details these configuration
settings.

| property | description |
| -------- | ----------- |
| retain_rtstats_raw[hours] | How long, in hours, to retain database entries of raw rtstats ingested, setting to `null` disables purging old data |
| retain_rtstats_hourly[days] | How long, in days, to retain database entries of aggregated hourly data. setting to `null` disables purging old data |
| retain_rtstats_daily[days] | How long, in days, to retain database entries of aggreated daily data. setting to `null` disables purging old data |
