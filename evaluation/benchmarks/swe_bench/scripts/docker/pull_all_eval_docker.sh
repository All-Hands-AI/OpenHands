#!/usr/bin/env bash
set -e

SET=$1
# check set is in ["full", "lite", "verified"]
if [ "$SET" != "full" ] && [ "$SET" != "lite" ] && [ "$SET" != "verified" ]; then
    echo "Error: argument 1 must be one of: full, lite, verified"
    exit 1
fi

input_file=evaluation/benchmarks/swe_bench/scripts/docker/all-swebench-${SET}-instance-images.txt
echo "Downloading images based on ${input_file}"
# Check if the file exists
if [ ! -f "$input_file" ]; then
    echo "Error: File '$input_file' not found"
    exit 1
fi

# Get total number of images
total_images=$(wc -l < "${input_file}")
counter=0

echo "Starting to pull ${total_images} images"

# Read the file line by line and pull each image
while IFS= read -r image; do
    # Skip empty lines or comments
    if [ -n "$image" ] && [[ ! "$image" =~ ^[[:space:]]*# ]]; then
        counter=$((counter + 1))
        echo "[${counter}/${total_images}] Pulling ${image}"
        docker pull "${image}"
        sleep 2
    fi
done < "${input_file}"

echo "Finished pulling all images"
