#!/bin/bash

if [ -n "${DEBUG}" ]; then set -eux; fi

PATH="${PATH}:$yarn_global_root/node_modules/npm/bin:$yarn_global_root/bin"
echo ${PATH}

# Process named arguments
while getopts ":-m:-e:" opt; do
  case ${opt} in
    -m ) llm_model="$OPTARG";;
    -e ) embeddings_model="$OPTARG";;
    \? ) echo "Invalid option: $OPTARG" 1>&2; exit 1;;
    : ) echo "Invalid option: $OPTARG requires an argument" 1>&2; exit 1;;
  esac
done
shift $((OPTIND -1))

# Access named arguments
echo "Default LLM model: $llm_model"
echo "Default Embeddings model: $embeddings_model"

which vite

if [ -n "${DEBUG}" ]; then
    vite --config vite.config.js --host 0.0.0.0 --port "${UI_HTTP_PORT:?}" \
        --clearScreen false --debug True
else
    vite --config vite.config.js --host 0.0.0.0 --port "${UI_HTTP_PORT:?}"
fi
