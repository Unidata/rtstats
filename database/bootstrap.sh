# setup databases

psql -c "create user nobody with unencrypted password 'secret';" -U postgres
psql -c "create user ldm with unencrypted password 'secret';" -U postgres

psql -c "create database rtstats;" -U postgres
psql -f init/rtstats.sql -U postgres rtstats
