#!/bin/bash


# API base URL
BASE_URL="https://api.all-hands.dev/v0"

# Get the list of runtimes
runtimes=$(curl --silent --location --request GET "${BASE_URL}/runtime/list" \
  --header "X-API-Key: ${ALLHANDS_API_KEY}" | jq -r '.runtimes | .[].runtime_id')

# Loop through each runtime and stop it
for runtime_id in $runtimes; do
  echo "Stopping runtime: ${runtime_id}"
  curl --silent --location --request POST "${BASE_URL}/runtime/stop" \
    --header "X-API-Key: ${ALLHANDS_API_KEY}" \
    --header "Content-Type: application/json" \
    --data-raw "{\"runtime_id\": \"${runtime_id}\"}"
  echo
done

echo "All runtimes have been stopped."
