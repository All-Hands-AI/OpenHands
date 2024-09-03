---
sidebar_position: 3
---

# 🧠 Main Agent and Capabilities

## CodeActAgent

### Description

This agent implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents’ **act**ions into a
unified **code** action space for both _simplicity_ and _performance_.

The conceptual idea is illustrated below. At each turn, the agent can:

1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
2. **CodeAct**: Choose to perform the task by executing code

- Execute any valid Linux `bash` command
- Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.

![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### Demo

https://github.com/All-Hands-AI/OpenHands/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_Example of CodeActAgent with `gpt-4-turbo-2024-04-09` performing a data science task (linear regression)_.
