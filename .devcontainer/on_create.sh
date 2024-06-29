#!/usr/bin/env bash
sudo apt install -y netcat
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.11
curl -sSL https://install.python-poetry.org | python3.11 -
poetry run pip install pysqlite3-binary