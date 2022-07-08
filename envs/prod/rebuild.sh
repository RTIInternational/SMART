#!/bin/bash
read -p "This script will delete the existing SMART database and restore the database to the last backup. Continue (yes/no)? " choice
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
docker-compose run --rm backend ./migrate.sh
cat /home/applications/SMART/envs/prod/backups/postgres_backup.sql| docker exec -i prod_postgres_1 psql -U postgres
docker-compose up -d