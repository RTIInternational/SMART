#!/bin/bash
read -p "This script will delete the existing SMART database and reset it to default. Continue (yes/no)? " choice
case "$choice" in
  yes|YES|Yes ) echo "Yes";;
  no|NO|No ) echo "No"; exit;;
  * ) echo "Invalid"; exit;;
esac

docker-compose down
docker volume rm vol_smart_pgdata_15_2 vol_smart_data
docker volume create vol_smart_pgdata_15_2
docker volume create vol_smart_data
docker-compose build
docker-compose run --rm backend ./migrate.sh
docker-compose run --rm backend ./seed_smart.sh
docker-compose up
