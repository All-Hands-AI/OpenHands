# MemCodeAct Agent

## Introduction

`memcodeact_agent` is a memory-enabled experimental agent built upon the foundation of the existing `codeact_agent`, incorporating memory functionalities.

## Inspiration and Research

The development of `memcodeact_agent` is inspired by two research papers in the field of generative AI and memory-augmented models:

1. **Extending Generative AI with Memory**
   - **Paper:** [Extending Generative AI with Memory](https://arxiv.org/pdf/2304.03442)
   - **Summary:** This paper explores methods to integrate long-term memory into generative AI models, enabling them to retain and utilize information from past interactions. The approach enhances the model's ability to maintain context over extended conversations, leading to more accurate and relevant outputs. Techniques such as memory slots, retrieval mechanisms, and memory encoding strategies are discussed to facilitate effective information storage and retrieval.

2. **MemGPT: Memory-Enhanced GPT Models**
   - **Paper:** [MemGPT: Memory-Enhanced GPT Models](https://arxiv.org/pdf/2310.08560)
   - **Summary:** MemGPT introduces a novel architecture that incorporates external memory modules into GPT models. This integration allows the model to access and update its memory dynamically during interactions. The results demonstrate significant improvements in tasks requiring information recall.

## Getting Started

### Prerequisites

- Configuration variables in `config.toml`, `agent.MemCodeactAgent` section:
  - `micro_agent_name`: Name of the micro agent to use.
  - `enable_memory`: Whether to enable long-term memory. Default is true for this agent.
  - `cache_prompt`: Whether to cache the prompt. Default is false for this agent.


- Optional environment variables:
  - `SANDBOX_ENV_GITHUB_TOKEN`: GitHub Personal Access Token with read-only permissions.

## Documentation

For detailed information on how to interact with the agent, refer to the [User Prompt](user_prompt.j2) and [System Prompt](system_prompt.j2) templates located within the agent's directory. These templates define the conversational flow and the agent's capabilities.

## Contribution

`memcodeact_agent` is an experimental agent designed for research and development purposes. Contributions are welcome!
