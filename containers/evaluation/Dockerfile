FROM ghcr.io/opendevin/sandbox:latest

RUN apt-get update && \
    apt-get install -y libffi-dev bash gcc git jq wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sfn /bin/bash /bin/sh
RUN mkdir -p /opendevin/logs && chmod 777 /opendevin/logs

# Setup Git
RUN git config --global user.email "swebench@pnlp.org"
RUN git config --global user.name "swebench"

# # Install Mamba/Conda
RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
# install to /opt/miniforge3
RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opt/miniforge3
RUN export PATH=/opt/miniforge3/bin:$PATH
RUN /opt/miniforge3/bin/mamba init bash

# Setup SWE-Bench Eval Env
RUN /bin/bash -c "/opt/miniforge3/bin/mamba create -n swe-bench-eval python==3.11.5 -y"
RUN /bin/bash -c ". /opt/miniforge3/etc/profile.d/conda.sh && conda activate swe-bench-eval && \
pip install requests python-dotenv GitPython datasets pandas beautifulsoup4 ghapi"
RUN /bin/bash -c ". /opt/miniforge3/etc/profile.d/conda.sh
&& conda config --set changeps1 False
&& conda config --append channels conda-forge"

CMD ["/bin/bash"]
