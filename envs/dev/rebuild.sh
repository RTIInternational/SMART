#!/bin/bash

docker-compose down
docker volume rm vol_smart_pgdata vol_smart_data
docker volume create vol_smart_pgdata
docker volume create vol_smart_data
docker-compose build
docker-compose run --rm backend ./migrate.sh
docker-compose run --rm backend ./seed_smart.sh
docker-compose up