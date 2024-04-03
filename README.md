<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

<div align="center">
  <a href="https://github.com/OpenDevin/OpenDevin/graphs/contributors"><img src="https://img.shields.io/github/contributors/opendevin/opendevin?style=for-the-badge" alt="Contributors"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/network/members"><img src="https://img.shields.io/github/forks/opendevin/opendevin?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/stargazers"><img src="https://img.shields.io/github/stars/opendevin/opendevin?style=for-the-badge" alt="Stargazers"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/issues"><img src="https://img.shields.io/github/issues/opendevin/opendevin?style=for-the-badge" alt="Issues"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/blob/main/LICENSE"><img src="https://img.shields.io/github/license/opendevin/opendevin?style=for-the-badge" alt="MIT License"></a>
</div>

<!-- PROJECT LOGO -->
<div align="center">
  <img src="./logo.png" alt="Logo" width="200" height="200">
  <h1 align="center">OpenDevin: Code Less, Make More</h1>
</div>




<!-- TABLE OF CONTENTS -->
<details>
  <summary>🗂️ Table of Contents</summary>
  <ol>
    <li><a href="#-mission">🎯 Mission</a></li>
    <li><a href="#-what-is-devin">🤔 What is Devin?</a></li>
    <li><a href="#-why-opendevin">🐚 Why OpenDevin?</a></li>
    <li><a href="#-project-status">🚧 Project Status</a></li>
      <a href="#-get-started">🚀 Get Started</a>
      <ul>
        <li><a href="#1-requirements">1. Requirements</a></li>
        <li><a href="#2-build-and-setup">2. Build and Setup</a></li>
        <li><a href="#3-run-the-application">3. Run the Application</a></li>
        <li><a href="#4-individual-server-startup">4. Individual Server Startup</a></li>
        <li><a href="#5-help">5. Help</a></li>
      </ul>
    </li>
    <li><a href="#%EF%B8%8F-research-strategy">⭐️ Research Strategy</a></li>
    <li><a href="#-how-to-contribute">🤝 How to Contribute</a></li>
    <li><a href="#-join-our-community">🤖 Join Our Community</a></li>
    <li><a href="#%EF%B8%8F-built-with">🛠️ Built With</a></li>
    <li><a href="#-license">📜 License</a></li>
  </ol>
</details>

## 🎯 Mission

[Project Demo Video](https://github.com/OpenDevin/OpenDevin/assets/38853559/71a472cc-df34-430c-8b1d-4d7286c807c9)


Welcome to OpenDevin, an open-source project aiming to replicate Devin, an autonomous AI software engineer who is capable of executing complex engineering tasks and collaborating actively with users on software development projects. This project aspires to replicate, enhance, and innovate upon Devin through the power of the open-source community.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🤔 What is Devin?
Devin represents a cutting-edge autonomous agent designed to navigate the complexities of software engineering. It leverages a combination of tools such as a shell, code editor, and web browser, showcasing the untapped potential of LLMs in software development. Our goal is to explore and expand upon Devin's capabilities, identifying both its strengths and areas for improvement, to guide the progress of open code models.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🐚 Why OpenDevin?
The OpenDevin project is born out of a desire to replicate, enhance, and innovate beyond the original Devin model. By engaging the open-source community, we aim to tackle the challenges faced by Code LLMs in practical scenarios, producing works that significantly contribute to the community and pave the way for future advancements.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🚧 Project Status

OpenDevin is currently a work in progress, but you can already run the alpha version to see the end-to-end system in action. The project team is actively working on the following key milestones:

- **UI**: Developing a user-friendly interface, including a chat interface, a shell demonstrating commands, and a web browser.
- **Architecture**: Building a stable agent framework with a robust backend that can read, write, and run simple commands.
- **Agent Capabilities**: Enhancing the agent's abilities to generate bash scripts, run tests, and perform other software engineering tasks.
- **Evaluation**: Establishing a minimal evaluation pipeline that is consistent with Devin's evaluation criteria.

After completing the MVP, the team will focus on research in various areas, including foundation models, specialist capabilities, evaluation, and agent studies.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🚀 Get Started

Getting started with the OpenDevin project is incredibly easy. Follow these simple steps to set up and run OpenDevin on your system:

### 1. Requirements
* Linux, Mac OS, or [WSL on Windows](https://learn.microsoft.com/en-us/windows/wsl/install)
* [Docker](https://docs.docker.com/engine/install/)
* [Python](https://www.python.org/downloads/) >= 3.11
* [NodeJS](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) >= 14.8

### 2. Build and Setup

- **Build the Project:** Begin by building the project, which includes setting up the environment and installing dependencies. This step ensures that OpenDevin is ready to run smoothly on your system.
    ```bash
    make build
    ```

- **Setup the Environment:** With just one command, configure OpenDevin by providing essential details such as the LLM API key, LLM Model name, and workspace directory. This straightforward setup process ensures that OpenDevin is tailored to your specific requirements.
    ```bash
    make setup-config
    ```

You'll need to choose your LLM model as part of this step. By default, we use OpenAI's gpt-4, but you can
use Anthropic's Claude, ollama, or any other LLM provider supported by LiteLLM. See the full
list of supported models at [docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers).

(Note: alternative models can be hard to work with. We will make LLM-specific available documentation available soon.
If you've gotten OpenDevin working with a model other than OpenAI's GPT models,
please [add your setup instructions here](https://github.com/OpenDevin/OpenDevin/issues/417).)

### 3. Run the Application

- **Run the Application:** Once the setup is complete, launching OpenDevin is as simple as running a single command. This command starts both the backend and frontend servers seamlessly, allowing you to interact with OpenDevin without any hassle.
    ```bash
    make run
    ```

### 4. Individual Server Startup

- **Start the Backend Server:** If you prefer, you can start the backend server independently to focus on backend-related tasks or configurations.
    ```bash
    make start-backend
    ```

- **Start the Frontend Server:** Similarly, you can start the frontend server on its own to work on frontend-related components or interface enhancements.
    ```bash
    make start-frontend
    ```

### 5. Help

- **Get Some Help:** Need assistance or information on available targets and commands? The help command provides all the necessary guidance to ensure a smooth experience with OpenDevin.
    ```bash
    make help
    ```

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## ⭐️ Research Strategy

Achieving full replication of production-grade applications with LLMs is a complex endeavor. Our strategy involves:

1. **Core Technical Research:** Focusing on foundational research to understand and improve the technical aspects of code generation and handling.
2. **Specialist Abilities:** Enhancing the effectiveness of core components through data curation, training methods, and more.
3. **Task Planning:** Developing capabilities for bug detection, codebase management, and optimization.
4. **Evaluation:** Establishing comprehensive evaluation metrics to better understand and improve our models.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🤝 How to Contribute

OpenDevin is a community-driven project, and we welcome contributions from everyone. Whether you're a developer, a researcher, or simply enthusiastic about advancing the field of software engineering with AI, there are many ways to get involved:

- **Code Contributions:** Help us develop the core functionalities, frontend interface, or sandboxing solutions.
- **Research and Evaluation:** Contribute to our understanding of LLMs in software engineering, participate in evaluating the models, or suggest improvements.
- **Feedback and Testing:** Use the OpenDevin toolset, report bugs, suggest features, or provide feedback on usability.

For details, please check [this document](./CONTRIBUTING.md).

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🤖 Join Our Community

Join our Slack workspace by filling out the [form](https://forms.gle/758d5p6Ve8r2nxxq6). Stay updated on OpenDevin's progress, share ideas, and collaborate with fellow enthusiasts and experts. Let's simplify software engineering together!

🐚 **Code less, make more with OpenDevin.**

[![Star History Chart](https://api.star-history.com/svg?repos=OpenDevin/OpenDevin&type=Date)](https://star-history.com/#OpenDevin/OpenDevin&Date)

## 🛠️ Built With

OpenDevin is built using a combination of powerful frameworks and libraries, providing a robust foundation for its development. Here are the key technologies used in the project:

![FastAPI](https://img.shields.io/badge/FastAPI-black?style=for-the-badge) ![uvicorn](https://img.shields.io/badge/uvicorn-black?style=for-the-badge) ![LiteLLM](https://img.shields.io/badge/LiteLLM-black?style=for-the-badge) ![Docker](https://img.shields.io/badge/Docker-black?style=for-the-badge) ![Ruff](https://img.shields.io/badge/Ruff-black?style=for-the-badge) ![MyPy](https://img.shields.io/badge/MyPy-black?style=for-the-badge) ![LlamaIndex](https://img.shields.io/badge/LlamaIndex-black?style=for-the-badge) ![React](https://img.shields.io/badge/React-black?style=for-the-badge)

Please note that the selection of these technologies is in progress, and additional technologies may be added or existing ones may be removed as the project evolves. We strive to adopt the most suitable and efficient tools to enhance the capabilities of OpenDevin.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 📜 License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

[contributors-shield]: https://img.shields.io/github/contributors/opendevin/opendevin?style=for-the-badge
[contributors-url]: https://github.com/OpenDevin/OpenDevin/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/opendevin/opendevin?style=for-the-badge
[forks-url]: https://github.com/OpenDevin/OpenDevin/network/members
[stars-shield]: https://img.shields.io/github/stars/opendevin/opendevin?style=for-the-badge
[stars-url]: https://github.com/OpenDevin/OpenDevin/stargazers
[issues-shield]: https://img.shields.io/github/issues/opendevin/opendevin?style=for-the-badge
[issues-url]: https://github.com/OpenDevin/OpenDevin/issues
[license-shield]: https://img.shields.io/github/license/opendevin/opendevin?style=for-the-badge
[license-url]: https://github.com/OpenDevin/OpenDevin/blob/main/LICENSE
