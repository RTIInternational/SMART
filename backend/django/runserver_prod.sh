#!/bin/bash

# wait for postgres to be ready
nc -z postgres 5432
n=$?
while [ $n -ne 0 ]; do
    sleep 1
    nc -z postgres 5432
    n=$?
done

# wait for frontend container to build dist files
while ping -c1 smart_frontend &>/dev/null; do
    sleep 1;
done

# init redis
python manage.py init_redis

# collect static files
python manage.py collectstatic -c --no-input

# start server
gunicorn -w 4 -b 0.0.0.0:8000 --timeout 86400 --worker-class gevent smart.wsgi
