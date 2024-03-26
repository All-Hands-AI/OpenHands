# OpenDevin Server

This is a WebSocket server that executes tasks using an agent.

## Install

Create a `.env` file with the contents

```sh
OPENAI_API_KEY=<YOUR OPENAI API KEY>
```

Install requirements:

```sh
python3.12 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Start the Server

```sh
uvicorn opendevin.server.listen:app --reload --port 3000
```

## Test the Server

You can use `websocat` to test the server: https://github.com/vi/websocat

```sh
websocat ws://127.0.0.1:3000/ws
{"action": "start", "args": {"task": "write a bash script that prints hello"}}
```

## Supported Environment Variables

```sh
OPENAI_API_KEY=sk-... # Your OpenAI API Key
MODEL_NAME=gpt-4-0125-preview # Default model for the agent to use
WORKSPACE_DIR=/path/to/your/workspace # Default path to model's workspace
```
