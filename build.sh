#!/bin/bash
set -e

cp pyproject.toml poetry.lock openhands
poetry build -v
