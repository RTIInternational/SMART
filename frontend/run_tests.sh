#!/bin/bash

echo "Checking ESLint...."
result=$(yarn run lint)
lint_exit_code=$?
echo "$result"

if [ $lint_exit_code -ne 0 ]; then
  echo "\nFix the above ESLint errors before running tests"
  exit 1
else
  echo "ESLint Styling Good. Running Tests..."
fi

yarn run test
