ARG node_version
ARG npm_version
FROM node:${node_version}-alpine as builder

ARG node_version
ARG npm_version
ARG debug

ENV DEBIAN_FRONTEND=noninteractive

COPY docker/openssl.cnf /etc/ssl/openssl.cnf

RUN if [ -n "$debug" ]; then set -eux; fi && \
    apk update && if [ -z "$debug" ]; then apk upgrade; fi && \
    apk --no-cache add git openssl ca-certificates && \
    mkdir -p /root/devin/.ssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /root/devin/.ssl/server_privkey.pem \
    -out /root/devin/.ssl/server_fullchain.pem \
    -config /etc/ssl/openssl.cnf && \
    rm -rf /var/cache/apk/*

ARG node_env
ARG node_options
ARG pm_cache_dir=/usr/local/share/.cache/yarn/v6
ARG build_dir
ARG build_dir=/opt/opendevin/build_ui

ENV NODE_ENV="$node_env"
ENV yarn_global_root=/usr/local/lib
ENV PATH="${PATH}:$yarn_global_root/node_modules/npm/bin:$yarn_global_root/bin"
ENV NODE_OPTIONS="$node_options"

WORKDIR $build_dir

RUN --mount=type=cache,target=$pm_cache_dir \
    if [ -n "$debug" ]; then set -eux; fi && \
    if [ -z .npmrc ]; then touch .npmrc; fi && \
    if [ -z "$debug" ]; then echo "loglevel=silent" | tee -a ./.npmrc; fi && \
    npm config set prefix "$yarn_global_root" && \
    npm config set audit false && \
    npm config set fund false && \
    npm install -g npm@${npm_version} && \
    yarn global add --prefix="$yarn_global_root" typescript vite

COPY .git ./../.git
COPY frontend/*.json .
COPY frontend/.npmrc .
COPY frontend/*.config.js .
COPY frontend/index.html .
COPY frontend/yarn.lock .
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/scripts ./scripts
COPY .env .

RUN --mount=type=cache,target=$pm_cache_dir \
    if [ -n "$debug" ]; then set -eux; fi && \
    yarn install && tsc

RUN rm -rf "$pm_cache_dir/*"

FROM node:${node_version}-alpine as serve

RUN if [ -n "$debug" ]; then set -eux; fi && \
    apk update && if [ -z "$debug" ]; then apk upgrade; fi && \
    apk --no-cache add git

ARG debug
ARG node_env
ARG node_options
ARG app_root=/opt/opendevin/ui

ENV DEBUG=$debug
ENV NODE_OPTIONS="$node_options"
ENV NODE_ENV=$node_env

ARG build_dir=/opt/opendevin/build_ui
ARG pm_cache_dir=/usr/local/share/.cache/yarn/v6

ENV yarn_global_root=/usr/local/lib
ENV PATH="${PATH}:$yarn_global_root/node_modules/npm/bin:$yarn_global_root/bin"

WORKDIR $build_dir

COPY --from=builder $build_dir .
COPY --from=builder $build_dir/yarn.lock $build_dir/yarn.lock
COPY --from=builder $build_dir/package.json $build_dir/package.json
COPY --from=builder $build_dir/.npmrc $build_dir/.npmrc
COPY --from=builder $build_dir/vite.config.js $build_dir/vite.config.js

COPY --from=builder /etc/ssl/openssl.cnf /etc/ssl/openssl.cnf
COPY --from=builder /root/devin/.ssl/server_privkey.pem /root/devin/.ssl/privkey.pem
COPY --from=builder /root/devin/.ssl/server_fullchain.pem /root/devin/.ssl/fullchain.pem

RUN --mount=type=cache,target=$pm_cache_dir \
    if [ -n "$debug" ]; then set -eux; fi && \
    npm config set prefix "${yarn_global_root}" && \
    npm config set audit false && \
    npm config set fund false && \
    yarn global add vite esbuild nx@latest @nx/react

RUN --mount=type=cache,target=$pm_cache_dir \
    if [ -n "$debug" ]; then set -eux; fi && \
    yarn add -P classnames webpack typescript


COPY frontend/vite.config.js $app_dir/vite.config.js

RUN --mount=type=cache,target=$build_dir/dist \
    echo "Finalizing build..." && \
    if [ -n "$debug" ]; then set -eux; fi && \
    rm -rf /var/lib/apt/lists/* && \
    npm cache clean --force && \
    yarn cache clean

COPY docker/devin/web_ui/entrypoint.sh /docker-entrypoint.sh
RUN --mount=type=cache,target=$build_dir/dist \
    if [ -n "$debug" ]; then set -eux; fi && \
    vite build --config vite.config.js --clearScreen false

ENTRYPOINT ["/bin/sh", "-c", "/docker-entrypoint.sh"]
CMD "-m ${DEFAULT_CHAT_MODEL} -e ${DEFAULT_EMBEDDINGS_MODEL} --"
