#!/bin/bash

# wait for postgres to be ready
nc -z postgres 5432
n=$?
while [ $n -ne 0 ]; do
    sleep 1
    nc -z postgres 5432
    n=$?
done

python ./manage.py seed_SMART