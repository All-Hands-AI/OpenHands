#!/bin/bash
set -e

LEVEL=$1
# three levels:
# - base, keyword "sweb.base"
# - env, keyword "sweb.env"
# - instance, keyword "sweb.eval"

if [ -z "$LEVEL" ]; then
    echo "Usage: $0 <cache_level>"
    echo "cache_level: base, env, or instance"
    exit 1
fi

NAMESPACE=xingyaoww
IMAGE_FILE="$(dirname "$0")/all-swebench-lite-instance-images.txt"

# Define a pattern based on the level
case $LEVEL in
    base)
        PATTERN="sweb.base"
        ;;
    env)
        PATTERN="sweb.base\|sweb.env"
        ;;
    instance)
        PATTERN="sweb.base\|sweb.env\|sweb.eval"
        ;;
    *)
        echo "Invalid cache level: $LEVEL"
        echo "Valid levels are: base, env, instance"
        exit 1
        ;;
esac

echo "Pulling docker images for [$LEVEL] level"

echo "Pattern: $PATTERN"
echo "Image file: $IMAGE_FILE"

# Read each line from the file, filter by pattern, and pull the docker image
grep "$PATTERN" "$IMAGE_FILE" | while IFS= read -r image; do
    echo "Pulling $NAMESPACE/$image into $image"
    docker pull $NAMESPACE/$image
    docker tag $NAMESPACE/$image $image
done
