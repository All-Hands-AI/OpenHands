# OpenDevin server
This is currently just a POC that starts an echo websocket inside docker, and
forwards messages between the client and the docker container.

## Start the Server
```
cd server
python -m pip install -r requirements.txt
uvicorn server:app --reload --port 3000
```

## Test the Server
You can use `websocat` to test the server: https://github.com/vi/websocat

```
websocat ws://127.0.0.1:3000/ws
{"source":"client","action":"start"}
```

### Test cases
We should be robust to these cases:
* Client connects, sends start command, agent starts up, client disconnects
* Client connects, sends start command, disconnects before agent starts
* Client connects, sends start command, agent disconnects (i.e. docker container is killed)
* Client connects, sends start command, agent starts up, client sends second start command

In each case, the client should be able to reconnect and send a start command
