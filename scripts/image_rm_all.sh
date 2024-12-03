set -euo pipefail
# set -x

if [ -z "$BASH_SOURCE" ]; then
  # NOTE: When running the script through Python's subprocess, BASH_SOURCE does not exist.
  thisFile="$0"
  if [ -z "$0" ]; then
    echo "ERROR: Could not deduce path of script"
    exit 1
  fi
else
  thisFile=$(readlink -f "$BASH_SOURCE")
fi
thisDir=$(dirname "$thisFile")

# Stop containers, since we can't delete an image of an open container.
$thisDir/image_stop_all.sh

# Delete container images.
# img_name_partial="all-hands"
img_name_partial="<none>"
found="$(docker images | (grep "$img_name_partial" | awk '{print $3}' || :))"

if [ -n "$found" ]; then
  echo "Deleting images: $found"
  docker rmi $found --force
fi
