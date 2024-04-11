# Using base image as the nodejs image from docker hub
FROM node:21.7.2-bookworm-slim

# Creating a working directory in the '/' (root) location
WORKDIR /OpenDevin

RUN apt-get update -y
RUN apt-get install -y curl make git python3.11 python3-pip
RUN curl -fsSL https://get.docker.com | sh
RUN python3 -m pip install poetry  --break-system-packages

COPY . .

RUN make build

ENTRYPOINT ["./entrypoint.sh"]
