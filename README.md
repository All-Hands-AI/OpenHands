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
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <img src="./logo.png" alt="Logo" width="200" height="200">
  <h1 align="center">OpenDevin: Code Less, Make More</h1>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>🗂️ Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">🐚 About OpenDevin</a>
      <ul>
        <li><a href="#project-status">🚧 Project Status</a></li>
      </ul>
    </li>
    <li>
      <a href="#get-started">🚀 Get Started</a>
      <ul>
        <li><a href="#1-build-and-setup">1. Build and Setup</a></li>
        <li><a href="#2-run-the-application">2. Run the Application</a></li>
        <li><a href="#3-individual-server-startup">3. Individual Server Startup</a></li>
        <li><a href="#4-help">4. Help</a></li>
      </ul>
    </li>
    <li><a href="#research-strategy">⭐️ Research Strategy</a></li>
    <li><a href="#how-to-contribute">🤝 How to Contribute</a></li>
    <li><a href="#join-our-community">🤖 Join Our Community</a></li>
    <li><a href="#built-with">🛠️ Built With</a></li>
    <li><a href="#license">📜 License</a></li>
  </ol>
</details>

## 🐚 About OpenDevin

[Project Demo Video](https://github.com/OpenDevin/OpenDevin/assets/38853559/5b1092cc-3554-4357-a279-c2a2e9b352ad)

OpenDevin is an open-source project that aims to replicate and enhance the capabilities of [Devin](https://www.cognition-labs.com/introducing-devin), an autonomous AI software engineer developed by Cognition Labs. Devin is designed to navigate the complexities of software engineering, leveraging a combination of tools such as a shell, code editor, and web browser to showcase the untapped potential of large language models (LLMs) in software development.

The primary goals of the OpenDevin project are:

1. **Replication**: To faithfully replicate the core functionality and capabilities of the original Devin model, providing a platform for further research and development.
2. **Enhancement**: To explore ways to expand upon Devin's abilities, identifying both its strengths and areas for improvement, with the goal of guiding the progress of open code models.
3. **Innovation**: To tackle the unique challenges faced by Code LLMs in practical scenarios, producing innovative solutions that contribute significantly to the open-source community and pave the way for future advancements.

By engaging the open-source community, the OpenDevin project aspires to become a collaborative effort that drives the evolution of AI-powered software engineering tools. Through a multifaceted research strategy, the team aims to advance the state of the art in areas such as core technical research, specialist abilities, task planning, and comprehensive evaluation.

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

### 1. Build and Setup

1. **Build the Project:** Begin by building the project, which includes setting up the environment and installing dependencies. This step ensures that OpenDevin is ready to run smoothly on your system.
    ```bash
    make build
    ```

2. **Setup the Environment:** With just one command, configure OpenDevin by providing essential details such as the LLM API key, LLM Model name, and workspace directory. This straightforward setup process ensures that OpenDevin is tailored to your specific requirements.
    ```bash
    make setup-config
    ```

### 2. Run the Application

3. **Run the Application:** Once the setup is complete, launching OpenDevin is as simple as running a single command. This command starts both the backend and frontend servers seamlessly, allowing you to interact with OpenDevin without any hassle.
    ```bash
    make run
    ```

### 3. Individual Server Startup

4. **Start the Backend Server:** If you prefer, you can start the backend server independently to focus on backend-related tasks or configurations.
    ```bash
    make start-backend
    ```

5. **Start the Frontend Server:** Similarly, you can start the frontend server on its own to work on frontend-related components or interface enhancements.
    ```bash
    make start-frontend
    ```

### 4. Help

6. **Help:** Need assistance or information on available targets and commands? The help command provides all the necessary guidance to ensure a smooth experience with OpenDevin.
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

![FastAPI](https://img.shields.io/badge/FastAPI-black?style=for-the-badge) ![uvicorn](https://img.shields.io/badge/uvicorn-black?style=for-the-badge) ![LiteLLM](https://img.shields.io/badge/LiteLLM-black?style=for-the-badge) ![Docker](https://img.shields.io/badge/Docker-black?style=for-the-badge) ![Ruff](https://img.shields.io/badge/Ruff-black?style=for-the-badge) ![MyPy](https://img.shields.io/badge/MyPy-black?style=for-the-badge) ![LangChain](https://img.shields.io/badge/LangChain-black?style=for-the-badge) ![LangChain](https://img.shields.io/badge/LlamaIndex-black?style=for-the-badge) ![React](https://img.shields.io/badge/React-black?style=for-the-badge)

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