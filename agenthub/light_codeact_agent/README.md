# LightCodeAct: A Simplified CodeAct Agent Framework

LightCodeAct is a simplified version of the CodeAct agent ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)). The original CodeAct idea consolidates LLM agents' **act**ions into a unified **code** action space for both *simplicity* and *performance*. LightCodeAct aims to make the agent more accessible and easier to work with for a wider range of language models, while still maintaining the core principles of the CodeAct framework.

LightCodeAct can:

1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
2. **CodeAct**: Choose to perform the task by executing code
   - Execute any valid Linux `bash` command
   - Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.

## Plugin System

To enhance LightCodeAct's capabilities with only access to `bash` action space, it leverages OpenDevin's plugin system:
- [Jupyter plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/jupyter): for IPython execution via bash command
- [SWE-agent tool plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/swe_agent_commands): Powerful bash command line tools for software development tasks introduced by [swe-agent](https://github.com/princeton-nlp/swe-agent).

## Simplifications

LightCodeAct is designed for less capable models that struggle with complex instructions. It focuses on core functionalities, providing a simpler interface to ensure effective performance with essential features.
