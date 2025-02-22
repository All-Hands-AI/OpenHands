#!/bin/bash
set -e
set +x

echo "checking hello world"
pwd
ls -lah

# Check if hello.sh exists
if [ ! -f hello.sh ]; then
    echo "hello.sh does not exist"
    exit 1
fi

# Check if it's executable
if [ ! -x hello.sh ]; then
    echo "hello.sh is not executable"
    exit 1
fi

# Run and check output
output=$(./hello.sh)
if [ "$output" != "hello world" ]; then
    echo "Expected 'hello world' but got: $output"
    exit 1
fi

exit 0
