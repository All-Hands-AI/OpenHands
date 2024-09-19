#!/bin/bash
set -eu

function version() {
	local version

	version=$(git tag --list 'v*' --sort=v:refname --merged|tail -1)
    if [ -z "$version" ]; then
        git rev-parse --short HEAD
    else
        echo "$version"
    fi
}

docker build --build-arg VERSION="${VERSION:-$(version)}" --output "type=local,dest=$PWD/dist" -t openhands-cli-build ./
