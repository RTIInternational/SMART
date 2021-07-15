#!/bin/bash
#
# Helper script for running isort formatter
# By default this script will run in --check mode
#   if --format is passed then script will format code

set -euo pipefail
IFS=$'\n\t'

if [[ $* == --format ]]; then
  isort -rc /code/
else
  set +e
  isort -rc --check-only /code/
  exitcode=$?
  set -e

  if [ $exitcode -ne 0 ]; then
    echo ""
    echo "Fix the above isort errors before running tests"
    exit 1
  fi
fi