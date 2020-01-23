#!/bin/bash
# WARNING: This is a convience script made for testing & debugging
# the production settings.  Do NOT run this in actual produciton
# or all of your data will be deleted!!!
docker-compose down
docker volume rm vol_smart_pgdata_prod vol_smart_data_prod
docker volume create vol_smart_pgdata_prod
docker volume create vol_smart_data_prod
docker volume create vol_smart_static_prod
docker-compose build
docker-compose run --rm smart_backend ./migrate.sh
docker-compose run --rm smart_backend ./seed_smart.sh
docker-compose up -d
docker-compose exec smart_backend python manage.py collectstatic --no-input