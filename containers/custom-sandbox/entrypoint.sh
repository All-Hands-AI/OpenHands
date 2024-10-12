#!/bin/bash
# this script is for dind in container but is not required
# the agent is smart enough and will try start the docker daemon
# if it is not already running

# start docker and wait for it to be ready
sudo service docker start
while ! sudo docker info > /dev/null 2>&1; do
    echo "waiting for docker to start..."
    sleep 1
done

# allow anyone to access the docker service
sudo chmod 666 /var/run/docker.sock

#
exec "$@"
