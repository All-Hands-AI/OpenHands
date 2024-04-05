FROM ubuntu:20.04

# https://github.com/princeton-nlp/SWE-bench/issues/15#issuecomment-1815392192
RUN apt-get update && \
    apt-get install -y bash gcc git jq wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN git config --global user.email "swebench@pnlp.org"
RUN git config --global user.name "swebench"

RUN apt update && apt install -y build-essential

# Create new user
RUN useradd -ms /bin/bash swe-bench
USER swe-bench
WORKDIR /home/swe-bench

# Setup Conda
ENV PATH="/home/swe-bench/miniconda3/bin:${PATH}"
ARG PATH="/home/swe-bench/miniconda3/bin:${PATH}"
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-`uname -m`.sh -O miniconda.sh \
    && mkdir ~/.conda \
    && bash miniconda.sh -b \
    && rm -f miniconda.sh
RUN conda --version

# Setup SWE-Bench Env
COPY environment.yml .
RUN conda env create -f environment.yml

# Add commands
COPY ./commands.sh .
RUN source commands.sh

# Some missing packages
RUN pip install datasets python-dotenv gitpython

RUN conda init bash

CMD ["/bin/bash"]
