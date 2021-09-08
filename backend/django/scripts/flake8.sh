#!/bin/bash
#
# Helper script for running flake8 linting
# This script will print all flake8 errors
set -euo pipefail
IFS=$'\n\t'

set +e
flake8 /code/ 
exitcode=$?
set -e

if [ $exitcode -ne 0 ]; then
  echo ""
  echo "Fix the above flake8 errors before running tests"
  exit 1
fi
