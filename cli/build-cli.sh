#!/bin/bash

set -euo pipefail

export GOPATH=
export GO111MODULE=on

#
name_table=(
"darwin/amd64:macos"
"darwin/arm64:macos"
"linux/amd64:linux"
"linux/arm64:linux"
"windows/amd64:windows"
"windows/arm64:windows"
)

bin_table=(
"darwin/amd64:openhands"
"darwin/arm64:openhands"
"linux/amd64:openhands"
"linux/arm64:openhands"
"windows/amd64:openhands.exe"
"windows/arm64:openhands.exe"
)

function lookup() {
	local os=$1
	local arch=$2
	local key="$os/$arch"
	shift
	shift
	local table=("$@")

	for kv in "${table[@]}"; do
		k="${kv%%:*}"
		v="${kv##*:}"
		if [ "$k" == "$key" ]; then
			echo "$v"
			return
		fi
	done
	echo "unknown-$os-$arch"
}

function version() {
	local version

	version=$(git tag --list 'v*' --sort=v:refname --merged|tail -1)
    if [ -z "$version" ]; then
        git rev-parse --short HEAD
    else
        echo "$version"
    fi
}

# TODO certificates are required for signing the binaries
function sign() {
	local os=$1

    case "$os" in
	darwin)
        echo "TODO signing for macos"
        ;;
    windows)
        echo "TODO signing for windows"
        ;;
    *)
        echo "$os requires no signing"
        ;;
    esac
}

function build() {
    local os=$1
    local arch=$2

	local name
	local bin
	local dir

	name=$(lookup "$os" "$arch" "${name_table[@]}")
	bin=$(lookup "$os" "$arch" "${bin_table[@]}")
	dir="dist/openhands-$name-$VERSION"

	mkdir -p "$dir"

	# update vars in source code
    extra="-X '${PKG}.AppVersion=$VERSION' -X '${PKG}.AppOS=$name' -X '${PKG}.SandBox=$SANDBOX' -X '${PKG}.Image=$IMAGE'"

	CGO_ENABLED=0 GOOS=$os GOARCH=$arch go build -o "$dir/$bin" -ldflags="-w -extldflags '-static' $extra" ./

	sign "$os" "$arch"
}

##
PKG="github.com/All-Hands-AI/OpenHands/cli/internal"

VERSION="${VERSION:-$(version)}"
SANDBOX="ghcr.io/all-hands-ai/runtime:0.9-nikolaik"
IMAGE="ghcr.io/all-hands-ai/openhands:0.9"

go fmt ./...
go vet ./...
go mod tidy
go test -short ./...

rm -rf dist/*

build darwin amd64
build windows amd64
build linux amd64

#
