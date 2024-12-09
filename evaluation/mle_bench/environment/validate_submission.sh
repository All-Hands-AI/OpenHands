#!/bin/bash

# This script is a tool for agents to submit a file to the grading server for validation.

# validate_submission.sh
# Usage: ./validate_submission.sh user_submission.csv

SUBMISSION_FILE=$1
SERVER_URL="http://localhost:5000/validate"

if [ -z "$SUBMISSION_FILE" ]; then
    echo "Usage: $0 <submission_file>"
    exit 1
fi

if [ ! -f "$SUBMISSION_FILE" ]; then
    echo "File $SUBMISSION_FILE does not exist."
    exit 1
fi

curl -X POST -F "file=@${SUBMISSION_FILE}" ${SERVER_URL}
