#!/bin/bash
#
# Helper script for running black formatter
# By default this script will run in --check mode
#   if --format is passed then script will format code
set -euo pipefail
IFS=$'\n\t'

if [[ $* == --format ]]; then
  black -t py36 /code/
else
  set +e
  black -t py36 --check /code/
  exitcode=$?
  set -e

  if [ $exitcode -ne 0 ]; then
    echo ""
    echo "Fix the above black errors before running tests"
    exit 1
  fi
fi
