<p align="center">
  <img alt="OpenDevin Logo" src="./logo.png" width="150" />
</p>

# OpenDevin: Code Less, Make More

![License](https://img.shields.io/badge/license-MIT-green)

[demo-video.webm](https://github.com/OpenDevin/OpenDevin/assets/38853559/5b1092cc-3554-4357-a279-c2a2e9b352ad)


## Mission 🎯
Welcome to OpenDevin, an open-source project aiming to replicate [Devin](https://www.cognition-labs.com/introducing-devin), an autonomous AI software engineer who is capable of executing complex engineering tasks and collaborating actively with users on software development projects. This project aspires to replicate, enhance, and innovate upon Devin through the power of the open-source community.

## Work in Progress

OpenDevin is still a work in progress. But you can run the alpha version to see things working end-to-end.

### Requirements
* [Docker](https://docs.docker.com/engine/install/)
* [Python](https://www.python.org/downloads/) >= 3.10
* [NodeJS](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) >= 14.8

### Installation
First, make sure Docker is running:
```bash
docker ps # this should exit successfully
```
Then start the backend:
```bash
export OPENAI_API_KEY="..."
export WORKSPACE_DIR="/path/to/your/project"
python -m pip install -r requirements.txt
uvicorn opendevin.server.listen:app --port 3000
```
Then in a second terminal:
```bash
cd frontend
npm install
npm run start -- --port 3001
```

You'll see OpenDevin running at localhost:3001

### Picking a Model
We use LiteLLM, so you can run OpenDevin with any foundation model, including OpenAI, Claude, and Gemini.
LiteLLM has a [full list of providers](https://docs.litellm.ai/docs/providers).

To change the model, set the `LLM_MODEL` and `LLM_API_KEY` environment variables.

For example, to run Claude:
```bash
export LLM_API_KEY="your-api-key"
export LLM_MODEL="claude-3-opus-20240229"
```

### Running on the Command Line
You can also run OpenDevin from your command line:
```
PYTHONPATH=`pwd` python opendevin/main.py -d ./workspace/ -i 100 -t "Write a bash script that prints 'hello world'"
```

## 🤔 What is [Devin](https://www.cognition-labs.com/introducing-devin)?

Devin represents a cutting-edge autonomous agent designed to navigate the complexities of software engineering. It leverages a combination of tools such as a shell, code editor, and web browser, showcasing the untapped potential of LLMs in software development. Our goal is to explore and expand upon Devin's capabilities, identifying both its strengths and areas for improvement, to guide the progress of open code models.

## 🐚 Why OpenDevin?

The OpenDevin project is born out of a desire to replicate, enhance, and innovate beyond the original Devin model. By engaging the open-source community, we aim to tackle the challenges faced by Code LLMs in practical scenarios, producing works that significantly contribute to the community and pave the way for future advancements.

## ⭐️ Research Strategy

Achieving full replication of production-grade applications with LLMs is a complex endeavor. Our strategy involves:

1. **Core Technical Research:** Focusing on foundational research to understand and improve the technical aspects of code generation and handling.
2. **Specialist Abilities:** Enhancing the effectiveness of core components through data curation, training methods, and more.
3. **Task Planning:** Developing capabilities for bug detection, codebase management, and optimization.
4. **Evaluation:** Establishing comprehensive evaluation metrics to better understand and improve our models.


## 🛠 Technology Stack

- **Sandboxing Environment:** Ensuring safe execution of code using technologies like Docker and Kubernetes.
- **Frontend Interface:** Developing user-friendly interfaces for monitoring progress and interacting with Devin, potentially leveraging frameworks like React or creating a VSCode plugin for a more integrated experience.

## 🚀 Next Steps

An MVP demo is urgent for us. Here are the most important things to do:

- UI: a chat interface, a shell demonstrating commands, a browser, etc.
- Architecture: an agent framework with a stable backend, which can read, write and run simple commands
- Agent: capable of generating bash scripts, running tests, etc.
- Evaluation: a minimal evaluation pipeline that is consistent with Devin's evaluation.

After finishing building the MVP, we will move towards research in different topics, including foundation models, specialist capabilities, evaluation, agent studies, etc.


## How to Contribute

OpenDevin is a community-driven project, and we welcome contributions from everyone. Whether you're a developer, a researcher, or simply enthusiastic about advancing the field of software engineering with AI, there are many ways to get involved:

- **Code Contributions:** Help us develop the core functionalities, frontend interface, or sandboxing solutions.
- **Research and Evaluation:** Contribute to our understanding of LLMs in software engineering, participate in evaluating the models, or suggest improvements.
- **Feedback and Testing:** Use the OpenDevin toolset, report bugs, suggest features, or provide feedback on usability.

For details, please check [this document](./CONTRIBUTING.md).

## Join Us
We use Slack to discuss. Feel free to fill in the [form](https://forms.gle/758d5p6Ve8r2nxxq6) if you would like to join the Slack organization of OpenDevin. We will reach out shortly if we feel you are a good fit to the current team! 

Stay updated on OpenDevin's progress, share your ideas, and collaborate with fellow enthusiasts and experts. Together, we can make significant strides towards simplifying software engineering tasks and creating more efficient, powerful tools for developers everywhere.

🐚 **Code less, make more with OpenDevin.**

[![Star History Chart](https://api.star-history.com/svg?repos=OpenDevin/OpenDevin&type=Date)](https://star-history.com/#OpenDevin/OpenDevin&Date)
