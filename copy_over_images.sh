#!/bin/bash

OWNER=18jeffreyma            # GitHub user/org that owns the image
IMAGE=swefficiency      # image/repository name
PAT="$GH_PAT"         # PAT with at least read:packages scope

#!/usr/bin/env bash
# migrate-ghcr-tags.sh
# -----------------------------------------------
# Copies all tags from ghcr.io/18jeffreyma/swefficiency
# to   docker.io/swefficiency/swefficiency, in parallel.
#
# REQUIRES these env vars to be set:
#   GH_PAT           – GitHub token with `read:packages` (and `repo` if private)
#   DOCKERHUB_USER   – your Docker Hub username
#   DOCKERHUB_PAT    – a Docker Hub PAT or password with push permission
#
# USAGE:
#   GH_PAT=xxxx DOCKERHUB_USER=me DOCKERHUB_PAT=yyyy ./migrate-ghcr-tags.sh
# -----------------------------------------------

set -euo pipefail

OWNER="18jeffreyma"
IMAGE="swefficiency"
SRC_REG="ghcr.io"
DST_REG="docker.io"
DST_REPO="swefficiency/swefficiency"

# ---------- 1. Log in to both registries ------------------------------------
echo "$GH_PAT"       | docker login "$SRC_REG" -u "$OWNER"          --password-stdin
echo "$DOCKERHUB_PAT"| docker login "$DST_REG" -u "$DOCKERHUB_USER" --password-stdin

# ---------- 2. Get all tags from GitHub Container Registry ------------------
echo "Fetching tag list from $SRC_REG/$OWNER/$IMAGE …"

# Short-lived bearer token scoped to the repository
BEARER_TOKEN=$(
  curl -s -u "${OWNER}:${GH_PAT}" \
    "https://${SRC_REG}/token?scope=repository:${OWNER}/${IMAGE}:pull" |
  jq -r '.token'
)

tags=()
url="https://${SRC_REG}/v2/${OWNER}/${IMAGE}/tags/list?n=100"
while [[ -n "$url" ]]; do
  # Grab this page of tags
  resp=$(curl -sSL -H "Authorization: Bearer ${BEARER_TOKEN}" "$url")
  mapfile -t page_tags < <(echo "$resp" | jq -r '.tags[]')
  tags+=("${page_tags[@]}")

  # Follow the RFC-5988 “next” Link header if present
  url=$(curl -sSLI -H "Authorization: Bearer ${BEARER_TOKEN}" "$url" \
        | awk -F'[<>]' '/rel="next"/ {print $2}')
done

if [[ ${#tags[@]} -eq 0 ]]; then
  echo "No tags found – nothing to do." >&2
  exit 1
fi

echo "Found ${#tags[@]} tag(s). Beginning migration …"

# ---------- 3. Pull, retag, and push – in parallel --------------------------
# Use all available CPU cores; override with JOBS=<n> env var if desired.
JOBS=${JOBS:-$(nproc)}

# Export variables for xargs subshells
export SRC_REG OWNER IMAGE DST_REG DST_REPO

printf '%s\n' "${tags[@]}" | xargs -n1 -P"$JOBS" -I{} bash -c '
    set -euo pipefail
    tag="$1"
    src="$SRC_REG/$OWNER/$IMAGE:$tag"
    dst="$DST_REG/$DST_REPO:$tag"

    echo "⏳  [$tag] pulling $src"
    docker pull --quiet "$src"

    echo "🔄  [$tag] tagging -> $dst"
    docker tag "$src" "$dst"

    echo "🚀  [$tag] pushing to Docker Hub"
    docker push --quiet "$dst"

    echo "🧹  [$tag] removing local images"
    docker rmi "$src" "$dst" || true

    echo "✅  [$tag] done"
' _ {}

echo "🎉  All tags migrated."
