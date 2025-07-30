#!/bin/bash


# this compares the old behaviour from the lint.yml with the new from "make check-all"

export OLD_OUTPUT=build/lint.yml.sh.output.txt
export NEW_OUTPUT=build/make-check-all.output.txt
mkdir -p build
rm -f $OLD_OUTPUT $NEW_OUTPUT

echo "Running original"
echo "Timing bash .github/workflows/lint.yml.sh..."
time_output=$(TIMEFORMAT='%3R'; time (bash .github/workflows/lint.yml.sh > $OLD_OUTPUT 2>&1) 2>&1)
echo "bash .github/workflows/lint.yml.sh took: ${time_output} seconds"

echo
echo "Running new version"
echo "Timing make check-all..."
time_output=$(TIMEFORMAT='%3R'; time (make check-all > $NEW_OUTPUT 2>&1) 2>&1)
echo "make check-all took: ${time_output} seconds"

echo
echo "Comparing them..."
diff $OLD_OUTPUT $NEW_OUTPUT
