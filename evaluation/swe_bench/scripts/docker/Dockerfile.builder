FROM ghcr.io/opendevin/sandbox:latest

RUN apt-get update && \
    apt-get install -y libffi-dev bash gcc git jq wget pkg-config libfreetype-dev libfreetype6 libfreetype6-dev rsync && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sfn /bin/bash /bin/sh
RUN mkdir -p /opendevin/logs && chmod 777 /opendevin/logs

# Setup Git
RUN git config --global user.email "swebench@swebench.ai"
RUN git config --global user.name "swebench"

CMD ["/bin/bash"]
# pushd evaluation/swe_bench
# docker build -t ghcr.io/opendevin/eval-swe-bench:builder -f ./scripts/docker/Dockerfile.builder .
