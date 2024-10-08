#!/bin/bash

# wait for postgres to be ready
nc -z postgres 5432
n=$?
while [ $n -ne 0 ]; do
    sleep 1
    nc -z postgres 5432
    n=$?
done

timestamp=$(date +"%Y%m%d_%H%M%S")
python -m memray run --follow-fork -o /var/log/memray_${timestamp}.bin ./manage.py runserver 0.0.0.0:8000 
