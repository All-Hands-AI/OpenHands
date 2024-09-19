#!/bin/bash
# Run the CLI based on the OS
# openhands [flags] WORKSPACE [-- [OPTION...] -- [COMMAND] [ARG...]]
#


set -euo pipefail

function find_run() {
	local os=$1
	local name=$2
	shift
	shift

	bin=$(find . -type f -path "./*${os}*/$name" -print -quit)
	if [[ -n "$bin" ]]; then
		"$bin" "$@"
	else
		echo "$name not found. Run 'make build' first."
	fi
}

##
os="$(uname | tr '[:upper:]' '[:lower:]')"
kernel="$(uname -r | tr '[:upper:]' '[:lower:]')"

case "$os" in
  linux*)
    case "$kernel" in
      *microsoft*)
	  	echo "Running on WSL"
		find_run windows openhands.exe "$@"
		;;
      *)
	  	echo "Running on Linux"
		find_run linux openhands "$@"
		;;
    esac
    ;;
  darwin*)
  	echo "Running on macOS"
	find_run macos openhands "$@"
	;;
  *)
  	echo "$os not supported"
	exit 1
	;;
esac

#
