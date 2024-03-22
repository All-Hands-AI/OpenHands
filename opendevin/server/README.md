# OpenDevin server
This is currently just a POC that starts an echo websocket inside docker, and
forwards messages between the client and the docker container.

## Start the Server
```
python -m pip install -r requirements.txt
uvicorn opendevin.server.listen:app --reload --port 3000
```

## Test the Server
You can use `websocat` to test the server: https://github.com/vi/websocat

```
websocat ws://127.0.0.1:3000/ws
{"action": "start", "args": {"task": "write a bash script that prints hello"}}
```

