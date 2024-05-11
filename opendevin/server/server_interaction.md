# Interacting with the OpenDevin Server

This document provides instructions on how to interact with the OpenDevin server using `websocat` for WebSocket communication and `curl` for REST API endpoints. Follow the steps below to start the server and send various actions and requests.

1. Start the server:
    ```sh
    uvicorn opendevin.server.listen:app --reload --port 3000
    ```
2.  Interact with WebSocket using `websocat`:
    - First, obtain an authentication token:
        ```sh
        TOKEN=$(curl -s -H "Authorization: Bearer 5ecRe7" http://127.0.0.1:3000/api/auth | jq -r '.token')
        ```
        **Note:** If `JWT_SECRET` is set, use its value instead of `5ecRe7`.
    - Then, connect to the WebSocket and send messages:
        ```sh
        websocat "ws://127.0.0.1:3000/ws?token=$TOKEN"
        ```
    Once connected, you can send various actions:
    - Initialize the agent:
        ```sh
        {"action": "initialize", "args": {"LLM_MODEL": "ollama/llama3:8b-instruct-q8_0", "AGENT": "CodeActAgent", "LANGUAGE": "en", "LLM_API_KEY": "ollama"}}
        ```
    - Start a new development task:
        ```sh
        {"action": "start", "args": {"task": "write a bash script that prints hello"}}
        ```
    - Send a message:
        ```sh
        {"action": "message", "args": {"content": "Hello, how are you?"}}
        ```
    - Write contents to a file:
        ```sh
        {"action": "write", "args": {"path": "./greetings.txt", "content": "Hello, OpenDevin?"}}
        ```
    - Read the contents of a file:
        ```sh
        {"action": "read", "args": {"path": "./greetings.txt"}}
        ```
    - Run a command:
        ```sh
        {"action": "run", "args": {"command": "ls -l"}}
        ```
    - Run an IPython command:
        ```sh
        {"action": "run_ipython", "args": {"command": "print('Hello, IPython!')"}}
        ```
    - Kill a background command:
        ```sh
        {"action": "kill", "args": {"id": "command_id"}}
        ```
    - Open a web page:
        ```sh
        {"action": "open", "args": {"url": "https://arxiv.org/html/2402.01030v2"}}
        ```
    - Search long-term memory:
        ```sh
        {"action": "recall", "args": {"query": "past projects"}}
        ```
    - Save a message to long-term memory:
        ```sh
        {"action": "save", "args": {"content": "Hello, OpenDevin!"}}
        ```
    - Add a task to the plan:
        ```sh
        {"action": "add_task", "args": {"task": "Implement feature X"}}
        ```
    - Update a task in the plan:
        ```sh
        {"action": "modify_task", "args": {"task_id": "task_id", "task": "Updated task description"}}
        ```
    - Change the agent's state:
        ```sh
        {"action": "change_agent_state", "args": {"state": "paused"}}
        ```
    - Finish the task:
        ```sh
        {"action": "finish"}
        ```
3. Interact with REST API endpoints using `curl`:
    - Get LiteLLM models:
        ```sh
        curl http://localhost:3000/api/litellm-models
        ```
    - Get supported agents:
        ```sh
        curl http://localhost:3000/api/agents
        ```
    - Get authentication token:
        ```sh
        curl -H "Authorization: Bearer 5ecRe7" http://localhost:3000/api/auth
        ```
        **Note:** If `JWT_SECRET` is set, use its value instead of `5ecRe7`.
    - Get messages:
        ```sh
        TOKEN=$(curl -s -H "Authorization: Bearer 5ecRe7" http://localhost:3000/api/auth | jq -r '.token')
        curl -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/messages
        ```
    - Get total message count:
        ```sh
        TOKEN=$(curl -s -H "Authorization: Bearer 5ecRe7" http://localhost:3000/api/auth | jq -r '.token')
        curl -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/messages/total
        ```
    - Delete messages:
        ```sh
        TOKEN=$(curl -s -H "Authorization: Bearer 5ecRe7" http://localhost:3000/api/auth | jq -r '.token')
        curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/messages
        ```
    - Refresh files:
        ```sh
        curl http://localhost:3000/api/refresh-files
        ```
    - Select a file:
        ```sh
        curl http://localhost:3000/api/select-file?file=<file_path>
        ```
    - Upload a file:
        ```sh
        curl -X POST -F "file=@<file_path>" http://localhost:3000/api/upload-file
        ```
    - Get plan:
        ```sh
        TOKEN=$(curl -s -H "Authorization: Bearer 5ecRe7" http://localhost:3000/api/auth | jq -r '.token')
        curl -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/plan
        ```
    - Get default configurations:
        ```sh
        curl http://localhost:3000/api/defaults
        ```
    **Note:** For the endpoints that require authentication (e.g., getting messages, deleting messages, getting plan), you need to obtain an authentication token first using the `/api/auth` endpoint with the appropriate `JWT_SECRET`. The obtained token is then used in the Authorization header for subsequent requests.
