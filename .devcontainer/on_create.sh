#!/usr/bin/env bash
sudo apt update
sudo apt install -y netcat
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.11
curl -sSL https://install.python-poetry.org | python3.11 -
cp /lib/x86_64-linux-gnu/libsqlite3.so.0 libsqlite3.so.0.backup
sudo cp /usr/local/lib/libsqlite3.so.0 /lib/x86_64-linux-gnu/libsqlite3.so.0
