#!/bin/bash

read -p "This script will delete the existing databse and restore with the latest backup (requires backup). Continue (yes/no)? " choice
case "$choice" in
  yes|YES|Yes ) echo "Yes";;
  no|NO|No ) echo "No"; exit;;
  * ) echo "Invalid"; exit;;
esac

docker-compose down
docker volume rm vol_smart_pgdata vol_smart_data
docker volume create vol_smart_pgdata
docker volume create vol_smart_data
docker-compose build
docker-compose up -d
docker exec --tty --interactive prod_postgres_1 /bin/sh -c "zcat /backups/last/smart-latest.sql.gz | psql --username=smart --dbname=smart -W"
docker-compose run --rm backend ./migrate.sh
docker-compose stop
docker-compose up -d
