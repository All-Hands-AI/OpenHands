ARG node_version
ARG npm_version
FROM node:${node_version}-alpine as builder

ARG node_version
ARG npm_version
ARG debug
ARG build_prod

ENV DEBIAN_FRONTEND=noninteractive

RUN if [ -n "$debug" ]; then set -eux; fi && \
    if [ -n "$build_prod" ]; then apk -q update && apk -q upgrade; fi

ARG node_env
ARG node_options
ARG pm_cache_dir=/usr/local/share/.cache/yarn/v6
ARG build_dir=/opt/opendevin/build_ui

ENV NODE_ENV="$node_env"
ENV yarn_global_root=/usr/local/lib
ENV PATH="${PATH}:$yarn_global_root/node_modules/npm/bin:$yarn_global_root/bin"
ENV NODE_OPTIONS="$node_options"

WORKDIR $build_dir

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
    if [ -z .npmrc ]; then touch .npmrc; fi && \
    if [ -z "$debug" ]; then echo "loglevel=silent" | tee -a ./.npmrc; fi && \
    sed -i 's/"packageManager": ".*@.*",/"packageManager": "yarn@'$(yarn --version)'",/' package.json && \
    npm config set prefix "$yarn_global_root" && \
    npm config set audit false && \
    npm config set fund false && \
    npm install -g npm@${npm_version} && \
    yarn global add --prefix="$yarn_global_root" classnames typescript webpack tsx \
    vite nx@latest @nx/react && \
    yarn install

RUN tsx && \
    vite build --config vite.config.js --clearScreen false && \
    echo "Finalizing build..." && \
    if [ -n "$debug" ]; then set -eux; fi && \
    if [ -n "$build_prod" ]; then rm -rf /var/lib/apt/lists/*; fi && \
    if [ -n "$build_prod" ]; then rm -rf $pm_cache_dir/*; fi && \
    if [ -z "$build_prod" ]; then npm cache clean --force; fi && \
    if [ -z "$build_prod" ]; then yarn cache clean; fi


FROM nginx as serve

ARG debug
ARG build_prod
ARG app_dir=/opt/opendevin/web

ENV DEBIAN_FRONTEND=noninteractive

COPY docker/openssl.cnf /etc/ssl/od_openssl.cnf

RUN if [ -n "$debug" ]; then set -eux; fi && \
    if [ -z "$build_prod" ]; then apt-get -q update && apt-get -qy upgrade; fi && \
    mkdir -p $app_dir/config/ssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $app_dir/config/ssl/mydomain-nginx.crt \
    -out $app_dir/config/ssl/mydomain-nginx.key \
    -config /etc/ssl/od_openssl.cnf > /dev/null && \
    rm -rf /var/lib/apt/lists/*

ARG debug
ARG app_root=/opt/opendevin/ui
ARG build_dir=/opt/opendevin/build_ui

ENV DEBUG=$debug

WORKDIR $build_dir

COPY --from=builder $build_dir/dist/ .

COPY docker/devin/web_ui/entrypoint.sh /docker-entrypoint.sh

ARG frontend_port

ENV FRONTEND_PORT=$frontend_port

EXPOSE $frontend_port

ENTRYPOINT ["/bin/sh", "-c", "/docker-entrypoint.sh"]
CMD "-m ${DEFAULT_CHAT_MODEL} -e ${DEFAULT_EMBEDDINGS_MODEL} --"
