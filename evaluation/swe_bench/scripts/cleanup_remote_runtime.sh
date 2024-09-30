#!/bin/bash


# API base URL
BASE_URL="https://runtime.eval.all-hands.dev"

# Get the list of runtimes
response=$(curl --silent --location --request GET "${BASE_URL}/list" \
  --header "X-API-Key: ${ALLHANDS_API_KEY}")

n_runtimes=$(echo $response | jq -r '.total')
echo "Found ${n_runtimes} runtimes. Stopping them..."

runtime_ids=$(echo $response | jq -r '.runtimes | .[].runtime_id')
# Loop through each runtime and stop it
counter=1
for runtime_id in $runtime_ids; do
  echo "Stopping runtime ${counter}/${n_runtimes}: ${runtime_id}"
  curl --silent --location --request POST "${BASE_URL}/stop" \
    --header "X-API-Key: ${ALLHANDS_API_KEY}" \
    --header "Content-Type: application/json" \
    --data-raw "{\"runtime_id\": \"${runtime_id}\"}"
  echo
  ((counter++))
done

echo "All runtimes have been stopped."
