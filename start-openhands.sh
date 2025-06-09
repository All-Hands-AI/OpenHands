export LLM_MODEL="openai/o4-mini-2025-04-16"

if [ -z "$LLM_API_KEY" ]; then
    echo "Please set the LLM_API_KEY environment variable to your API key."
    exit 1
fi

export SANDBOX_VOLUMES="$(pwd):/workspace:rw"
echo "Starting OpenHands with the following configuration:"
echo "LLM_MODEL: $LLM_MODEL"
echo "LLM_API_KEY: $LLM_API_KEY"
echo "SANDBOX_VOLUMES: $SANDBOX_VOLUMES"

sudo docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_MODEL=$LLM_MODEL \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.39
