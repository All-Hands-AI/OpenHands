#!/bin/bash

# Python3 setup - use $HOME instead of ~ when referring to your home directory
venvactivate="$HOME/python3/venv/OpenDevin/bin/activate"

# Param variables with some defaults
host="localhost"
port="3000"
model="gpt-3.5-turbo-0125"
workspace=""
apikey=""

# Log paths
uvicornlog="$HOME/opendevin-uvicorn.log"
npmlog="$HOME/opendevin-npm.log"


usage() {
  echo "Launch OpenDevin, the autonomous AI software engineer who is cable of executing complex engineering tasks."
  echo "Usage: $0 --host [IP] --port [PORT] --model [LLM_MODEL] --workspace <WORKSPACE_PATH> --apikey <API_KEY>"
  exit 1;
}

cleanup() {
  echo ""
  echo "Terminating uvicorn:$uvicorn_pid, npm:$npm_pid"
  kill -SIGINT $uvicorn_pid $npm_pid
  wait $uvicorn_pid $npm_pid
  exit 1
}

trap cleanup SIGINT

if [[ ! -f ./requirements.txt ]]; then
    echo "Error: Missing files. Have you switched to the OpenDevin project directory?"
    exit 1
fi


# Check for no params given
if [[ $# -eq 0 ]]; then
  usage
  exit 1
fi


# Get params
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      host="$2"
      shift 2
      ;;
    --port)
      port="$2"
      shift 2
      ;;
    --model)
      model="$2"
      shift 2
      ;;
    --workspace)
      workspace="$2"
      shift 2
      ;;
    --apikey)
      apikey="$2"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

# Check the required params have been given
if [[ -z $apikey || -z $workspace ]]; then
  usage
fi

if [[ ! -f $venvactivate ]]; then
    echo "Error: Virtual environment activate script not found!"
    echo "Path: $venvactivate"
    exit 1
fi

echo "Launching OpenDevin..."
echo "Model: $model"
echo "Host: $host"

source $venvactivate

# export environment variables
export OPENAI_API_KEY=$apikey
export WORKSPACE_DIR=$workspace
export LLM_MODEL=$model
export VITE_TERMINAL_WS_URL="ws://$host:$port/ws"

echo "VITE Terminal: $VITE_TERMINAL_WS_URL"

# Start uvicorn server
uvicorn opendevin.server.listen:app --port $port --host "$host" >> "$uvicornlog" 2>&1 &
uvicorn_pid=$!
echo "uvicorn running(PID $uvicorn_pid) $host : $port"

# Start frontend
npmport=$(($port + 1))
cd ./frontend
npm run start -- --port $npmport --host "$host" >> "$npmlog" 2>&1 &
npm_pid=$!
echo "frontend running(PID $npm_pid) $host : $npmport"
echo ""
echo "Logging: $uvicornlog"
echo "Logging: $npmlog"
echo "Press ^C to terminate"

wait $uvicorn_pid $npm_pid

#Deactivate Python venv
deactivate

cleanup()
