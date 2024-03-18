# Phase 1: End-to-End Prototype
We want to get an end-to-end prototype working as soon as possible.
This will give us a point to build from,
even if it can only complete basic tasks, like writing a small
shell script.

We believe the following features comprise a usable MVP:

## Frontend
The frontend should allow the user to input a prompt, and watch the
backend work to complete the task.

Features:
[x] A chat interface for the user to input prompts
[x] A shell which displays commands that are being run
[ ] The ability to stop the running task

## Backend
The backend should be a simple, single-socket websocket server.
It should accept incoming connections from the frontend, and handle
two types of messages:
[ ] An initial prompt
[ ] A stop command from the user

The backend should also:
[ ] Use an env variable to choose the LLM model
[ ] Use env variables for LLM credentials
[ ] Pass the prompt and stop command to an agent (below)

## Agent
The agent will take care of the actual logic of interacting with an LLM
to solve the user's task.

The agent should be able to take the following actions:
[ ] Read files
[ ] Write files
[ ] Run commands
[ ] Declare the task complete

# Phase 2: More complex tasks
Once we have a working prototype, we can start to move towards feature parity with Devin.

## Frontend
[ ] Implement a browser
[ ] LLM model switcher
[ ] LLM credentials input
[ ] User preferences in localstorage

## Backend
[ ] An API for switching LLM models
[ ] Allow user to add additional info/hints as the Agent is working

## Agent
[ ] Ability to load pages in the browser
[ ] Ability to interact with webpages
[ ] Run multiple processes simultaneously (e.g. `node server.js` and then `curl localhost:3000`)
[ ] Track current working directory
[ ] Regular `git commit`s

# Phase 3: Benchmark and Iterate
Once we have a usable demo, we'll need to benchmark against SWE-bench,
and create some regression tests to ensure solutions improve as we make changes.

