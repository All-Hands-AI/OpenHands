#!/bin/bash
set -eo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CASES_DIR=$SCRIPT_DIR/cases

# iterate over cases dir
for case in $(ls $CASES_DIR); do
  # run the case
  echo "Running case: $case"
done
