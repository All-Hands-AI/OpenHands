[English](README.md) | [中文](docs/README-zh.md)

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
  </br>
  <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2etftj1dd-X1fDL2PYIVpsmJZkqEYANw"><img src="https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge" alt="Join our Slack community"></a>
  <a href="https://discord.gg/mBuDGRzzES"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community"></a>
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

## ⚠️ Caveats and Warnings

- OpenDevin is still an alpha project. It is changing very quickly and is unstable. We are working on getting a stable release out in the coming weeks.
- OpenDevin will issue many prompts to the LLM you configure. Most of these LLMs cost money--be sure to set spending limits and monitor usage.
- OpenDevin runs `bash` commands within a Docker sandbox, so it should not affect your machine. But your workspace directory will be attached to that sandbox, and files in the directory may be modified or deleted.
- Our default Agent is currently the MonologueAgent, which has limited capabilities, but is fairly stable. We're working on other Agent implementations, including [SWE Agent](https://swe-agent.com/). You can [read about our current set of agents here](./docs/Agents.md).

## 🚀 Get Started

The easiest way to run OpenDevin is inside a Docker container.

To start the app, run these commands, replacing `$(pwd)/workspace` with the path to the code you want OpenDevin to work with.

```bash
# Your OpenAI API key, or any other LLM API key
export LLM_API_KEY="sk-..."

# The directory you want OpenDevin to modify. MUST be an absolute path!
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -e LLM_API_KEY \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal=host-gateway \
    ghcr.io/opendevin/opendevin:0.3.1
```

You'll find opendevin running at `http://localhost:3000`.

If you want to use the (unstable!) bleeding edge, you can use `ghcr.io/opendevin/opendevin:main` as the image.

See [Development.md](Development.md) for instructions on running OpenDevin without Docker.

Having trouble? Check out our [Troubleshooting Guide](./docs/guides/Troubleshooting.md).

## 🤖 LLM Backends

OpenDevin can work with any LLM backend.
For a full list of the LM providers and models available, please consult the
[litellm documentation](https://docs.litellm.ai/docs/providers).

The `LLM_MODEL` environment variable controls which model is used in programmatic interactions.
But when using the OpenDevin UI, you'll need to choose your model in the settings window (the gear
wheel on the bottom left).

The following environment variables might be necessary for some LLMs:

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_API_VERSION`

We have a few guides for running OpenDevin with specific model providers:

- [ollama](./docs/guides/LocalLLMs.md)
- [Azure](./docs/guides/AzureLLMs.md)

If you're using another provider, we encourage you to open a PR to share your setup!

**Note on Alternative Models:**
The best models are GPT-4 and Claude 3. Current local and open source models are
not nearly as powerful. When using an alternative model,
you may see long wait times between messages,
poor responses, or errors about malformed JSON. OpenDevin
can only be as powerful as the models driving it--fortunately folks on our team
are actively working on building better open source models!

**Note on API retries and rate limits:**
Some LLMs have rate limits and may require retries. OpenDevin will automatically retry requests if it receives a 429 error or API connection error.
You can set LLM_NUM_RETRIES, LLM_RETRY_MIN_WAIT, LLM_RETRY_MAX_WAIT environment variables to control the number of retries and the time between retries.
By default, LLM_NUM_RETRIES is 5 and LLM_RETRY_MIN_WAIT, LLM_RETRY_MAX_WAIT are 3 seconds and respectively 60 seconds.

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

Now we have both Slack workspace for the collaboration on building OpenDevin and Discord server for discussion about anything related, e.g., this project, LLM, agent, etc.

- [Slack workspace](https://join.slack.com/t/opendevin/shared_invite/zt-2etftj1dd-X1fDL2PYIVpsmJZkqEYANw)
- [Discord server](https://discord.gg/mBuDGRzzES)

If you would love to contribute, feel free to join our community (note that now there is no need to fill in the [form](https://forms.gle/758d5p6Ve8r2nxxq6)). Let's simplify software engineering together!

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
