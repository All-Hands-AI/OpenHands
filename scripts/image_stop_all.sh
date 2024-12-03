set -euo pipefail
# set -x

# Stop all swe-agent containers.
img_name_partial="swe-agent-task-env-"
found="$(docker ps -a | (grep "$img_name_partial" || :) | cut -d " " -f 1)"

if [ -n "$found" ]; then
  echo "Stopping containers: $found"
  docker rm $(docker stop $found)
fi
