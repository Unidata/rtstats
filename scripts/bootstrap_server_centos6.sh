# daryl and Mike Schmidt worked through this on 20 April 2017 to get this installed
# at Unidata.  This script was copied from bootstrap_server.sh, which was done for
# RHEL7 at the time last November.
set echo
yum -y install git

cd /opt
git clone https://github.com/akrherz/rtstats.git
cd rtstats/config
cp -f settings.json-in settings.json

cd
wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
sh Miniconda2-latest-Linux-x86_64.sh -f -b -p /opt/miniconda2

rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm
rpm -ivh https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-6-x86_64/pgdg-centos96-9.6-3.noarch.rpm

yum -y install postgresql96-server httpd php mod_ssl \
libxml2-devel gcc-c++ byacc make perl bc lftp \
postgis2_96 memcached

# anytree is not provided by anaconda at this time, so we pip it
/opt/miniconda2/bin/pip install anytree
/opt/miniconda2/bin/conda config --add channels conda-forge
/opt/miniconda2/bin/conda install -y psycopg2 pygeoip matplotlib twisted python-memcached

echo "127.0.0.1 rtstats.local" >> /etc/hosts

cd /etc/httpd/conf.d
cp -f /opt/rtstats/config/rtstats-vhost.conf .
cp -f /opt/rtstats/config/rtstats-vhost.inc .

# TODO resolve letsencrypt certs used by rtstats

chkconfig httpd on
# This fails due to the TODO above with letsencrypt
service httpd start

chkconfig postgresql-9.6 on
sudo -u postgres /usr/pgsql-9.6/bin/initdb -D /var/lib/pgsql/9.6/data
service postgresql-9.6 start
cd /opt/rtstats/database
sudo -u postgres sh bootstrap.sh
/opt/miniconda2/bin/python schema_manager.py

# TODO: set /opt/miniconda2/bin in front of LDM's PATH
# TODO: add "pqact /opt/rtstats/ldm/pqact.conf" to LDM's ldmd.conf
sudo -u ldm crontab /opt/rtstats/scripts/ldm.crontab
