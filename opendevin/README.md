# OpenDevin Architecture

This directory contains the core components of OpenDevin.

The key classes in OpenDevin are:
* LLM: brokers all interactions with large language models. Works with any underlying completion model, thanks to LiteLLM.
* Agent: responsible for looking at the current State, and producing an Action that moves one step closer toward the end-goal.
* AgentController: initializes the Agent, manages State, and drive the main loop that pushes the Agent forward, step by step
* State: represents the current state of the Agent's task. Includes things like the current step, a history of recent events, the Agent's long-term plan, etc
* EventStream: a central hub for Events, where any component can publish Events, or listen for Events published by other components
  * Event: an Action or Observeration
      * Action: represents a request to e.g. edit a file, run a command, or send a message
      * Observation: represents information collected from the environment, e.g. file contents or command output
* Runtime: responsible for performing Actions, and sending back Observations
    * Sandbox: the part of the runtime responsible for running commands, e.g. inside of Docker
* Server: brokers OpenDevin sessions over HTTP, e.g. to drive the frontend
    * Session: holds a single EventStream, a single AgentController, and a single Runtime. Generally represents a single task (but potentially including several user prompts)
    * SessionManager: keeps a list of active sessions, and ensures requests are routed to the correct Session

## Control Flow
The EventStream serves as the backbone for all communication in OpenDevin.

```mermaid
flowchart LR
  AgentController--Actions-->EventStream
  EventStream--Observations-->AgentController
  Runtime--Observations-->EventStream
  EventStream--Actions-->Runtime
  Frontend--Actions-->EventStream
```
