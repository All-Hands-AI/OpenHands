# Build the runtime image.

set -euo pipefail

cd "$(dirname "$0")"/..

# Prepare: Copy over all the code etc. into containers/runtime
export LOG_LEVEL=DEBUG # debugging
poetry run python3 openhands/runtime/utils/runtime_build.py \
    --base_image nikolaik/python-nodejs:python3.12-nodejs22 \
    --build_folder containers/runtime

# Actually build the container image (will be named `<none>`)
(cd containers/runtime && docker build .)
