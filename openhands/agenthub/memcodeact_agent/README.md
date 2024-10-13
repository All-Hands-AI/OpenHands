# MemCodeAct Agent

## Introduction

`memcodeact_agent` is a memory-enabled experimental agent built upon the foundation of the existing `codeact_agent`. Designed to enhance the capabilities of autonomous agents, `memcodeact_agent` incorporates advanced memory functionalities inspired by recent advancements in generative AI research. This agent leverages memory to improve task execution, context retention, and overall performance, making it more adept at handling complex and extended interactions.

## Features

- **Memory Integration:** Retains context across multiple interactions, allowing for more coherent and contextually aware responses.
- **Enhanced Action Parsing:** Utilizes a memory-augmented action parser to interpret and execute complex commands effectively.
- **Improved Task Management:** Manages and retrieves past actions and observations to inform current decision-making processes.
- **Experimental Capabilities:** Serves as a platform for testing and refining memory-related functionalities in AI agents.

## Inspiration and Research

The development of `memcodeact_agent` is inspired by two pivotal research papers in the field of generative AI and memory-augmented models:

1. **Extending Generative AI with Memory**
   - **Paper:** [Extending Generative AI with Memory](https://arxiv.org/pdf/2304.03442)
   - **Summary:** This paper explores methods to integrate long-term memory into generative AI models, enabling them to retain and utilize information from past interactions. The approach enhances the model's ability to maintain context over extended conversations, leading to more accurate and relevant outputs. Techniques such as memory slots, retrieval mechanisms, and memory encoding strategies are discussed to facilitate effective information storage and retrieval.

2. **MemGPT: Memory-Enhanced GPT Models**
   - **Paper:** [MemGPT: Memory-Enhanced GPT Models](https://arxiv.org/pdf/2310.08560)
   - **Summary:** MemGPT introduces a novel architecture that incorporates external memory modules into GPT models. This integration allows the model to access and update its memory dynamically during interactions. The paper details the implementation of memory layers, attention mechanisms for memory retrieval, and training methodologies that enable the model to learn from both its internal parameters and external memory. The results demonstrate significant improvements in tasks requiring long-term dependency understanding and information recall.

## Getting Started

### Prerequisites

- Python 3.10+
- Required environment variables:
  - `SANDBOX_ENV_GITHUB_TOKEN`: GitHub Personal Access Token with read-only permissions.

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/All-Hands-AI/OpenHands.git
   ```

2. **Navigate to the Agent Directory:**
   ```bash
   cd OpenHands/odie/openhands/agenthub/memcodeact_agent
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. **Configure Environment Variables:**
   Set the `SANDBOX_ENV_GITHUB_TOKEN` in your environment variables to enable GitHub interactions.

2. **Run the Agent:**
   ```bash
   python memcodeact_agent.py
   ```

3. **Interact with the Agent:**
   Follow the prompts to execute tasks. The agent will utilize its memory capabilities to provide more coherent and contextually aware responses.

## Documentation

For detailed information on how to interact with the agent, refer to the [User Prompt](user_prompt.j2) and [System Prompt](system_prompt.j2) templates located within the agent's directory. These templates define the conversational flow and the agent's capabilities.

## Contribution

`memcodeact_agent` is an experimental agent designed for research and development purposes. Contributions are welcome! Please ensure that any changes adhere to the project's coding standards and are accompanied by appropriate tests.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
