#!/bin/bash

[[ ! -z "${DEBUG}" ]]; set -eux

if [ -f "${MITMPROXY_DIR}/mitmproxy-ca.pem" ]; then
  f="${MITMPROXY_DIR}/mitmproxy-ca.pem"
else
  f="${MITMPROXY_DIR}"
fi
# usermod -o -u mitmproxy -g mitmproxy mitmproxy

if [[ "$1" = "mitmdump" || "$1" = "mitmproxy" || "$1" = "mitmweb" ]]; then
  exec gosu mitmproxy "$@"
else
  exec "$@"
fi
