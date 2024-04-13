ARG version
FROM python:3.11-bullseye as wheelbuilder
ARG version

LABEL org.opencontainers.image.description="mitmproxy (mitmproxy.org) version specific build"
LABEL org.opencontainers.image.version="mitmproxy v${version}"
LABEL org.opencontainers.image.author="lehcode <53556648+lehcode@users.noreply.github.com>"

ARG proxy_wheel

ADD https://downloads.mitmproxy.org/${version}/${proxy_wheel} /wheels/

SHELL ["/bin/sh", "-c"]

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    if [ ! -z "${DEBUG}" ]; then set -eux; fi && \
    pip install -q wheel && \
    pip wheel --wheel-dir /wheels /wheels/${proxy_wheel}

FROM python:3.11-slim-bullseye as exec

ARG mitmproxy_dir
ARG uid
ARG gid

ENV MITMPROXY_DIR=${mitmproxy_dir}

SHELL ["/bin/sh", "-c"]

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    if [ ! -z "${DEBUG}" ]; then set -eux; fi && \
    groupadd -g ${gid} mitmproxy && \
    useradd -m -u ${uid} -g ${gid} mitmproxy && \
    apt update && apt -qy upgrade && \
    apt install -qy --no-install-recommends gosu nano && \
    rm -rf /var/lib/apt/lists/*

COPY ./docker/mitmproxy/entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 775 /usr/local/bin/docker-entrypoint.sh

COPY --from=wheelbuilder /wheels /wheels

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    if [ ! -z "${DEBUG}" ]; then set -eux; fi && \
    pip install -q --no-index --find-links=/wheels mitmproxy && \
    rm -rf /wheels

VOLUME ${mitmproxy_dir}

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

CMD ["mitmproxy"]
