#!/bin/bash


# API base URL
BASE_URL="https://runtime.eval.all-hands.dev"

# Get the list of runtimes
response=$(curl --silent --location --request GET "${BASE_URL}/list" \
  --header "X-API-Key: ${ALLHANDS_API_KEY}")

n_runtimes=$(echo $response | jq -r '.total')
echo "Found ${n_runtimes} runtimes. Stopping them..."

runtime_ids=$(echo $response | jq -r '.runtimes | .[].runtime_id')

# Function to stop a single runtime
stop_runtime() {
  local runtime_id=$1
  local counter=$2
  echo "Stopping runtime ${counter}/${n_runtimes}: ${runtime_id}"
  curl --silent --location --request POST "${BASE_URL}/stop" \
    --header "X-API-Key: ${ALLHANDS_API_KEY}" \
    --header "Content-Type: application/json" \
    --data-raw "{\"runtime_id\": \"${runtime_id}\"}"
  echo
}
export -f stop_runtime
export BASE_URL ALLHANDS_API_KEY n_runtimes

# Use GNU Parallel to stop runtimes in parallel
echo "$runtime_ids" | parallel -j 16 --progress stop_runtime {} {#}

echo "All runtimes have been stopped."
