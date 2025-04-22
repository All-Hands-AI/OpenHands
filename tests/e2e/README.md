# How to start e2e tests

## Run the auth server

```bash
poetry run python tests/e2e/auth_server.py
```

## Setup env

```bash
# JWT Secret
RUN_MODE=DEV
THESIS_AUTH_SERVER_URL=http://localhost:5000
```

## Start the backend server

```bash
LOG_LEVEL=debug make start-backend
```

## Start the tests

```bash
poetry run python tests/e2e/test_e2e.py
```

Note that you can pass an existing CONVERSATION_ID to re-connect with its corresponding runtime. Each `test_e2e.py` process is a conversation, simulating the behavior of different sessions on the frontend, chatting with the LLM.

Eg:

```bash
CONVERSATION_ID=ae06d30226da4b4390f6d2767dbfd0ca poetry run python tests/e2e/test_e2e.py
```
