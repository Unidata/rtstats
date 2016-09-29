# setup databases

psql -c 'create user nobody;' -U postgres
psql -c 'create user ldm;' -U postgres

psql -c "create database rtstats;" -U postgres
psql -f init/rtstats.sql -U ldm -q rtstats
