FROM python:3.11-bookworm


# For OpenHands agents to explore the dataset directories, please download the full benchmark [here](https://buckeyemailosu-my.sharepoint.com/:u:/g/personal/chen_8336_buckeyemail_osu_edu/EQuA6uJ3CtRHvRfZ2GiN1tYBRVJE4DSUD10MW61fr7HuSQ?e=sCBegG) and unzip it with password `scienceagentbench`.
# **Please DO NOT redistribute the unzipped data files online.**
# It will download a benchmark.zip file to the current directory.
# unzip it and put the benchmark folder under evaluation/scienceagentbench/

RUN mkdir -p /benchmark
COPY benchmark /benchmark

RUN mkdir -p /workspace
WORKDIR /workspace

# pushd evaluation/scienceagentbench
# docker build -t xingyaoww/openhands-eval-scienceagentbench .
# popd
