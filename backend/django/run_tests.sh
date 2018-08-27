#!/bin/bash

# wait for postgres to be ready
nc -z postgres 5432
n=$?
while [ $n -ne 0 ]; do
    sleep 1
    nc -z postgres 5432
    n=$?
done

echo "Checking Flake8...."
result=$(flake8 --ignore E501,W503 .)
echo "$result"

if [ -n "$result" ]; then
  echo "\nFix the above PEP8 errors before running tests"
  exit 1
else
  echo "Flake8 Good. Running Tests..."
fi

coverage run -m py.test "$@"
coverage report -m --skip-covered
