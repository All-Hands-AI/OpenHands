FROM --platform=linux/amd64 mlebench-env

# Do not modify the following block of arg-env pairs. The evaluation infrastructure will
# periodically download the contents of these directories for logging purposes.

# Where the agent should write its `submission.csv`
ARG SUBMISSION_DIR=/home/submission
ENV SUBMISSION_DIR=${SUBMISSION_DIR}

# Where the agent's logs should be written
ARG LOGS_DIR=/home/logs
ENV LOGS_DIR=${LOGS_DIR}

# Where the agent should write its code
ARG CODE_DIR=/home/code
ENV CODE_DIR=${CODE_DIR}

# Where the agent code should exist
ARG AGENT_DIR=/home/agent
ENV AGENT_DIR=${AGENT_DIR}

ARG CONDA_ENV_NAME=agent
ARG PYTHON_VERSION=3.11
ARG OD_VERSION=v2.1.0
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p ${LOGS_DIR} ${AGENT_DIR} ${CODE_DIR} ${SUBMISSION_DIR} && \
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && \
    chmod 700 /tmp/get-docker.sh && \
    /tmp/get-docker.sh && \
    sudo usermod -aG docker nonroot && \
    git clone --branch ${OD_VERSION} --single-branch https://github.com/thesofakillers/OpenHands.git ${AGENT_DIR}

WORKDIR ${AGENT_DIR}

# Assumes that the `agent` conda env already exists, which is created in the `mlebench-env` base image.
RUN conda install -y -n ${CONDA_ENV_NAME} -c conda-forge nodejs=18.17.1 && \
    conda run -n ${CONDA_ENV_NAME} pip install poetry>=1.8 && \
    conda run -n ${CONDA_ENV_NAME} poetry install && \
    conda run -n ${CONDA_ENV_NAME} poetry add build && \
    conda clean -afy

COPY setup.py start.py templates.py utils.py start.sh build.sh ${AGENT_DIR}/
COPY entrypoint.sh /agent_entrypoint.sh

RUN chmod +x /agent_entrypoint.sh

# Allow the agent to do `sudo /build.sh`, but restrict it from reading or editing the file.
RUN echo "ALL ALL=NOPASSWD: ${AGENT_DIR}/build.sh" >> /etc/sudoers && \
    chmod 711 ${AGENT_DIR}/build.sh

# run the agent's entrypoint script instead (which also runs root entrypoint)
ENTRYPOINT ["/agent_entrypoint.sh"]
