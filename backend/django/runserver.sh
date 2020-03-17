#!/bin/bash

# wait for postgres to be ready
nc -z postgres 5432
n=$?
while [ $n -ne 0 ]; do
    sleep 1
    nc -z postgres 5432
    n=$?
done

# init redis
python manage.py init_redis

# start server
python ./manage.py runserver 0.0.0.0:8000
