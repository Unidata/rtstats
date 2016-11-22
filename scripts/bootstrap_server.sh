# daryl followed this on 22 Nov 2016 on a fresh RHEL 7.3 VM and it appeared to
# work OK
set echo
yum -y install git

cd /opt
git clone https://github.com/akrherz/rtstats.git
cd rtstats/config
cp -f settings.json-in settings.json

rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
rpm -ivh https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-redhat96-9.6-3.noarch.rpm

yum -y install git postgresql96-server httpd php mod_ssl \
libxml2-devel gcc-c++ byacc make perl bc lftp python-twisted-web \
pytz python-psycopg2 python-GeoIP postgis2_96 memcached python-requests \
python-pandas postgresql96-server python-memcached python-pip

pip install anytree

echo "127.0.0.1 rtstats.local" >> /etc/hosts

cd /etc/httpd/conf.d
cp -f /opt/rtstats/config/rtstats-vhost.conf .
cp -f /opt/rtstats/config/rtstats-vhost.inc .

# TODO resolve letsencrypt certs used by rtstats

systemctl enable httpd
systemctl start httpd

systemctl enable postgresql-9.6
sudo -u postgres /usr/pgsql-9.6/bin/initdb -D /var/lib/pgsql/9.6/data
systemctl start postgresql-9.6
cd /opt/rtstats/database
sudo -u postgres sh bootstrap.sh
python schema_manager.py

# TODO: add "pqact /opt/rtstats/ldm/pqact.conf" to LDM's ldmd.conf
sudo -u ldm crontab /opt/rtstats/scripts/ldm.crontab
