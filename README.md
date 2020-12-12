# rtstats

Unidata rtstats revamp, see discussion at @Unidata/unidata-usercomm#2

[![Build Status](https://github.com/Unidata/rtstats/workflows/Install%20and%20Test/badge.svg)](https://github.com/Unidata/rtstats/actions)

A public demonstration of this code is [here](https://rtstatstest.unidata.ucar.edu)

## Installation

This software makes the following assumptions.

1. RHEL/centos 7.3 64bit server, subscribed to EPEL and PGRPMS 9.6 yum repos
2. selinux is not enabled
3. this repository is checked out to `/opt/rtstats`
4. LDM is installed and setup to receive rtstats
5. 10 GB of space in `/`, 100 GB of space in `/var/lib/pgsql`
6. Firewall has been configured to allow TCP port 388 and either 80 or 443

This software has three primary components that can be run on a single VM or
spread over three instances.

1. LDM ingest script, which parses rtstats and mines into a database
2. A database that stores the information
3. A website with tools and web services that provide users access to the database
and queries backend HTTP services provided by LDM ingest process

For the purposes of this installation document, we'll assume that all three run
on the same server.  A [bootstrap_server.sh](scripts/bootstrap_server.sh) shell
script file exists with the setup process.

## `config/settings.json` options

Various codes within this repository get their runtime configuration from
the `config/settings.json` file.  The following table details these configuration
settings.

| property | description |
| -------- | ----------- |
| retain_rtstats_raw[hours] | How long, in hours, to retain database entries of raw rtstats ingested, setting to `null` disables purging old data |
| retain_rtstats_hourly[days] | How long, in days, to retain database entries of aggregated hourly data. setting to `null` disables purging old data |
| retain_rtstats_daily[days] | How long, in days, to retain database entries of aggreated daily data. setting to `null` disables purging old data |
