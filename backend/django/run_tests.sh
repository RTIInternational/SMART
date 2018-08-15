#!/bin/bash

# wait for postgres to be ready
nc -z postgres 5432
n=$?
while [ $n -ne 0 ]; do
    sleep 1
    nc -z postgres 5432
    n=$?
done

result=$(find . -name \*.py -exec pycodestyle --show-source --show-pep8 --ignore=E402,E501,W503,E722,W605 {} +)
echo "$result"

if [ -n "$result" ]; then
  echo "\nFix the above PEP8 errors before running tests"
  exit 1
fi

coverage run -m py.test "$@"
coverage report -m --skip-covered
