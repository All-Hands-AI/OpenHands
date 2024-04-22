> 警告：此说明文件可能已过时。应将 README.md 视为真实的来源。如果您注意到差异，请打开一个拉取请求以更新此说明文件。

[English](../README.md) | [中文](README-zh.md)

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
  <img src="../logo.png" alt="Logo" width="200" height="200">
  <h1 align="center">OpenDevin：少写代码，多创作</h1>
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

## 🎯 使命

[Project Demo Video](https://github.com/OpenDevin/OpenDevin/assets/38853559/71a472cc-df34-430c-8b1d-4d7286c807c9)

欢迎来到 OpenDevin，一个开源项目，旨在复制 Devin，一款自主的 AI 软件工程师，能够执行复杂的工程任务，并与用户积极合作，共同进行软件开发项目。该项目立志通过开源社区的力量复制、增强和创新 Devin。

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🤔 Devin 是什么？

Devin 代表着一种尖端的自主代理程序，旨在应对软件工程的复杂性。它利用诸如 shell、代码编辑器和 Web 浏览器等工具的组合，展示了在软件开发中利用 LLMs（大型语言模型）的未开发潜力。我们的目标是探索和拓展 Devin 的能力，找出其优势和改进空间，以指导开源代码模型的进展。

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🐚 为什么选择 OpenDevin？

OpenDevin 项目源于对复制、增强和超越原始 Devin 模型的愿望。通过与开源社区的互动，我们旨在解决 Code LLMs 在实际场景中面临的挑战，创作出对社区有重大贡献并为未来进步铺平道路的作品。

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🚧 项目状态

OpenDevin 目前仍在进行中，但您已经可以运行 alpha 版本来查看端到端系统的运行情况。项目团队正在积极努力实现以下关键里程碑：

- **用户界面（UI）**：开发用户友好的界面，包括聊天界面、演示命令的 shell 和 Web 浏览器。
- **架构**：构建一个稳定的代理框架，具有强大的后端，可以读取、写入和运行简单的命令。
- **代理能力**：增强代理的能力，以生成 bash 脚本、运行测试和执行其他软件工程任务。
- **评估**：建立一个与 Devin 评估标准一致的最小评估流水线。

在完成 MVP 后，团队将专注于各个领域的研究，包括基础模型、专家能力、评估和代理研究。

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## ⚠️ 注意事项和警告

- OpenDevin 仍然是一个 alpha 项目。它变化很快且不稳定。我们正在努力在未来几周发布稳定版本。
- OpenDevin 会向您配置的 LLM 发出许多提示。大多数 LLM 都需要花费金钱，请务必设置花费限制并监控使用情况。
- OpenDevin 在 Docker 沙箱中运行 `bash` 命令，因此不应影响您的计算机。但您的工作区目录将附加到该沙箱，并且目录中的文件可能会被修改或删除。
- 我们默认的代理目前是 MonologueAgent，具有有限的功能，但相当稳定。我们正在开发其他代理实现，包括 [SWE 代理](https://swe-agent.com/)。您可以[在这里阅读我们当前的代理集合](./docs/documentation/Agents.md)。

## 🚀 开始

开始使用 OpenDevin 项目非常简单。按照以下简单步骤在您的系统上设置和运行 OpenDevin：

运行 OpenDevin 最简单的方法是在 Docker 容器中。
您可以运行：

```bash
# 您的 OpenAI API 密钥，或任何其他 LLM API 密钥
export LLM_API_KEY="sk-..."

# 您想要 OpenDevin 修改的目录。必须是绝对路径！
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -e LLM_API_KEY \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/opendevin/opendevin:latest
```

将 `$(pwd)/workspace` 替换为您希望 OpenDevin 使用的代码路径。

您可以在 `http://localhost:3000` 找到正在运行的 OpenDevin。

请参阅[Development.md](Development.md)以获取在没有 Docker 的情况下运行 OpenDevin 的说明。

## 🤖 LLM 后端

OpenDevin 可以与任何 LLM 后端配合使用。
要获取提供的 LM 提供商和模型的完整列表，请参阅
[litellm 文档](https://docs.litellm.ai/docs/providers)。

`LLM_MODEL` 环境变量控制在编程交互中使用哪个模型，
但在 OpenDevin UI 中选择模型将覆盖此设置。

对于某些 LLM，可能需要以下环境变量：

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_API_VERSION`

**关于替代模型的说明：**
某些替代模型可能比其他模型更具挑战性。
不要害怕，勇敢的冒险家！我们将很快公布 LLM 特定的文档，指导您完成您的探险。
如果您已经掌握了除 OpenAI 的 GPT 之外的模型使用技巧，
我们鼓励您[与我们分享您的设置说明](https://github.com/OpenDevin/OpenDevin/issues/417)。

还有[使用 ollama 运行本地模型的文档](./docs/documentation/LOCAL_LLM_GUIDE.md)。

## ⭐️ 研究策略

利用 LLMs 实现生产级应用程序的完全复制是一个复杂的任务。我们的策略包括：

1. **核心技术研究：** 专注于基础研究，以了解和改进代码生成和处理的技术方面。
2. **专业能力：** 通过数据整理、训练方法等手段增强核心组件的效能。
3. **任务规划：** 开发能力，用于错误检测、代码库管理和优化。
4. **评估：** 建立全面的评估指标，以更好地了解和改进我们的模型。

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🤝 如何贡献

OpenDevin 是一个社区驱动的项目，我们欢迎所有人的贡献。无论您是开发人员、研究人员，还是对利用人工智能推动软件工程领域发展充满热情的人，都有许多参与方式：

- **代码贡献：** 帮助我们开发核心功能、前端界面或沙盒解决方案。
- **研究和评估：** 为我们对软件工程中的 LLMs 的理解做出贡献，参与评估模型，或提出改进意见。
- **反馈和测试：** 使用 OpenDevin 工具集，报告错误，提出功能建议，或就可用性提供反馈。

详情请查看[此文档](./CONTRIBUTING.md)。

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🤖 加入我们的社区

现在我们既有 Slack 工作空间用于协作构建 OpenDevin，也有 Discord 服务器用于讨论与项目、LLM、Agent 等相关的任何事情。

- [Slack 工作空间](https://join.slack.com/t/opendevin/shared_invite/zt-2etftj1dd-X1fDL2PYIVpsmJZkqEYANw)
- [Discord 服务器](https://discord.gg/mBuDGRzzES)

如果你愿意贡献，欢迎加入我们的社区（请注意，现在无需填写[表格](https://forms.gle/758d5p6Ve8r2nxxq6)）。让我们一起简化软件工程！

🐚 **少写代码，用 OpenDevin 创造更多。**

[![Star History Chart](https://api.star-history.com/svg?repos=OpenDevin/OpenDevin&type=Date)](https://star-history.com/#OpenDevin/OpenDevin&Date)

## 🛠️ 技术栈

OpenDevin 使用了一系列强大的框架和库的组合，为其开发提供了坚实的基础。以下是项目中使用的关键技术：

![FastAPI](https://img.shields.io/badge/FastAPI-black?style=for-the-badge) ![uvicorn](https://img.shields.io/badge/uvicorn-black?style=for-the-badge) ![LiteLLM](https://img.shields.io/badge/LiteLLM-black?style=for-the-badge) ![Docker](https://img.shields.io/badge/Docker-black?style=for-the-badge) ![Ruff](https://img.shields.io/badge/Ruff-black?style=for-the-badge) ![MyPy](https://img.shields.io/badge/MyPy-black?style=for-the-badge) ![LlamaIndex](https://img.shields.io/badge/LlamaIndex-black?style=for-the-badge) ![React](https://img.shields.io/badge/React-black?style=for-the-badge)

请注意，这些技术的选择正在进行中，随着项目的发展，可能会添加其他技术或移除现有技术。我们致力于采用最合适和最有效的工具，以增强 OpenDevin 的功能。

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 📜 许可证

根据 MIT 许可证分发。有关更多信息，请参阅 [`LICENSE`](./LICENSE)。

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
