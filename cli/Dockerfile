# syntax=docker/dockerfile:1

###
FROM golang:1.23.1-alpine AS build
RUN apk add --no-cache bash

ARG VERSION
ENV VERSION=${VERSION}

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN ./build-cli.sh

###
FROM scratch
COPY --from=build /app/dist /

CMD [ "bash" ]
