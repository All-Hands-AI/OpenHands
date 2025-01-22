#!/usr/bin/env bash
sudo apt update
sudo apt install -y netcat
sudo add-apt-repository -y ppa:deadsnakes/ppa
curl -sSL https://install.python-poetry.org | python3.12 -

# WAS working:
#sudo add-apt-repository -y ppa:deadsnakes/ppa \
#    && apt-get update \
#    && apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip \
#    && ln -s /usr/bin/python3.12 /usr/bin/python

# See: https://github.com/SmartManoj/Kevin/issues/122#issuecomment-2540482254
git config --global --add safe.directory /workspaces/OpenHands
