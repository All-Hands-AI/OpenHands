#!/bin/bash
# Script will delete all repositories and tags in your Docker Hub account
set -e

# Set username and password from command-line arguments
UNAME=$1
UPASS=$2

# Get token to interact with Docker Hub
TOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"username": "'${UNAME}'", "password": "'${UPASS}'"}' https://hub.docker.com/v2/users/login/ | jq -r .token)

# Ensure token retrieval was successful
if [[ -z "$TOKEN" ]]; then
    echo "Failed to obtain authentication token. Please check your credentials."
    exit 1
fi

# Get list of repositories for that user account
echo "Listing repositories in Docker Hub account '${UNAME}':"
REPO_LIST=$(curl -s -H "Authorization: JWT ${TOKEN}" "https://hub.docker.com/v2/repositories/${UNAME}/?page_size=10000" | jq -r '.results|.[]|.name')
if [[ -z "$REPO_LIST" ]]; then
    echo "No repositories found for user '${UNAME}' or failed to fetch repositories."
    exit 1
fi

# Loop through each repository and delete its tags and the repository itself
for rep in ${REPO_LIST}; do
    echo "Processing repository: ${UNAME}/${rep}"

    # Get all tags for the repository
    IMAGES=$(curl -s -H "Authorization: JWT ${TOKEN}" "https://hub.docker.com/v2/repositories/${UNAME}/${rep}/tags/?page_size=100")
    IMAGE_TAGS=$(echo $IMAGES | jq -r '.results|.[]|.name')

    # Delete each tag
    for tag in ${IMAGE_TAGS}; do
        echo "Deleting tag: ${UNAME}/${rep}:${tag}"
        curl -s -X DELETE -H "Authorization: JWT ${TOKEN}" "https://hub.docker.com/v2/repositories/${UNAME}/${rep}/tags/${tag}/"
    done

    # Delete the repository itself
    echo "Deleting repository: ${UNAME}/${rep}"
    curl -s -X DELETE -H "Authorization: JWT ${TOKEN}" "https://hub.docker.com/v2/repositories/${UNAME}/${rep}/" || {
        echo "Failed to delete repository '${UNAME}/${rep}'. Please check permissions or API limits."
    }
    sleep 1
done

echo "Script execution completed."
