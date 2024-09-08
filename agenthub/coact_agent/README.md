# CoAct Multi-Agent Framework

 This folder implements a multi-agent workflow inspired by the CoAct framework ([paper](https://arxiv.org/abs/2406.13381)), that provides a robust structure for defining, planning, and executing tasks using multiple agents.

 ## Agents

 1. `CoActPlannerAgent`:
     - is responsible for exploring and creating a global plan. It can replan if there are issues with the previous one.
     - has full capabilities of [CodeActAgent](https://github.com/All-Hands-AI/OpenHands/tree/main/agenthub/codeact_agent).
 2. `CoActExecutorAgent`:
     - is responsible for executing the proposed plan. Facing issues with the plan, it can request for a new one.
     - also has full capabilities of [CodeActAgent](https://github.com/All-Hands-AI/OpenHands/tree/main/agenthub/codeact_agent).
