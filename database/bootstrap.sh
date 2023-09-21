# setup databases

psql -c "create user nobody with password 'secret';" -U postgres
psql -c "create user ldm with password 'secret';" -U postgres

createdb -O ldm -U postgres rtstats
psql -f init/rtstats.sql -U ldm rtstats
