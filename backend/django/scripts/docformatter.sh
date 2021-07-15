#!/bin/bash
#
# Helper script for running docformatter
# By default this script will run in --check mode
#   if --format is passed then script will format code
set -euo pipefail
IFS=$''

if [[ $* == --format ]]; then
  docformatter -r -i --wrap-summaries 88 --wrap-descriptions 88 /code/
else
  set +e
  docformatter -r -c --wrap-summaries 88 --wrap-descriptions 88 /code/
  exitcode=$?
  set -e

  if [ $exitcode -ne 0 ]; then
    echo ""
    echo "Fix the above docformatter errors before running tests"
    exit 1
  fi
fi