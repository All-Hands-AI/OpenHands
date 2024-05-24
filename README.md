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
  <a href="https://github.com/OpenDevin/OpenDevin/graphs/contributors"><img src="https://img.shields.io/github/contributors/opendevin/opendevin?style=for-the-badge&color=blue" alt="Contributors"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/network/members"><img src="https://img.shields.io/github/forks/opendevin/opendevin?style=for-the-badge&color=blue" alt="Forks"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/stargazers"><img src="https://img.shields.io/github/stars/opendevin/opendevin?style=for-the-badge&color=blue" alt="Stargazers"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/issues"><img src="https://img.shields.io/github/issues/opendevin/opendevin?style=for-the-badge&color=blue" alt="Issues"></a>
  <a href="https://github.com/OpenDevin/OpenDevin/blob/main/LICENSE"><img src="https://img.shields.io/github/license/opendevin/opendevin?style=for-the-badge&color=blue" alt="MIT License"></a>
  <br/>
  <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2i1iqdag6-bVmvamiPA9EZUu7oCO6KhA"><img src="https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge" alt="Join our Slack community"></a>
  <a href="https://discord.gg/ESHStjSjD4"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community"></a>
  <br/>
  <a href="https://huggingface.co/spaces/OpenDevin/evaluation"><img src="https://img.shields.io/badge/SWE--bench%20Lite-25.0%25-green?style=for-the-badge" alt="SWE-bench "></a>
  <a href="https://codecov.io/github/opendevin/opendevin?branch=main"><img alt="CodeCov" src="https://img.shields.io/codecov/c/github/opendevin/opendevin?style=for-the-badge"></a>
</div>

<!-- PROJECT LOGO -->
<div align="center">
  <img src="./docs/static/img/logo.png" alt="Logo" width="200" height="200">
  <h1 align="center">OpenDevin: Code Less, Make More</h1>
  <a href="https://opendevin.github.io/OpenDevin/"><img src="https://img.shields.io/badge/Documentation-OpenDevin-blue?logo=googledocs&logoColor=white&style=for-the-badge" alt="Check out the documentation"></a>
</div>
<hr>

Welcome to OpenDevin, a platform for autonomous software engineers, powered by AI and LLMs.

OpenDevin agents collaborate with human developers to write code, fix bugs, and ship features.

![App screenshot](./docs/static/img/screenshot.png)

## ⚡ Getting Started
The easiest way to run OpenDevin is inside a Docker container. It works best with the most recent version of Docker, `26.0.0`.
You must be using Linux, Mac OS, or WSL on Windows.

To start the app, run these commands, replacing `$(pwd)/workspace` with the directory you want OpenDevin to work with.

```bash
# The directory you want OpenDevin to work with. MUST be an absolute path!
export WORKSPACE_BASE=$(pwd)/workspace;
```

> [!WARNING]  
> OpenDevin runs bash commands within a Docker sandbox, so it should not affect your machine. 
> But your workspace directory will be attached to that sandbox, and files in the directory may be modified or deleted.

```bash
docker run \
    -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    ghcr.io/opendevin/opendevin:0.5
```

You'll find OpenDevin running at [http://localhost:3000](http://localhost:3000).

## 🚀 Documentation

To learn more about the project, and for tips on using OpenDevin,
**check out our [documentation](https://opendevin.github.io/OpenDevin/)**.

There you'll find resources on how to use different LLM providers (like ollama and Anthropic's Claude),
troubleshooting resources, and advanced configuration options.

## 🤝 How to Contribute

OpenDevin is a community-driven project, and we welcome contributions from everyone.
Whether you're a developer, a researcher, or simply enthusiastic about advancing the field of
software engineering with AI, there are many ways to get involved:

- **Code Contributions:** Help us develop new agents, core functionality, the frontend and other interfaces, or sandboxing solutions.
- **Research and Evaluation:** Contribute to our understanding of LLMs in software engineering, participate in evaluating the models, or suggest improvements.
- **Feedback and Testing:** Use the OpenDevin toolset, report bugs, suggest features, or provide feedback on usability.

For details, please check [CONTRIBUTING.md](./CONTRIBUTING.md).

## 🤖 Join Our Community

Whether you're a developer, a researcher, or simply enthusiastic about OpenDevin, we'd love to have you in our community.
Let's make software engineering better together!

- [Slack workspace](https://join.slack.com/t/opendevin/shared_invite/zt-2ggtwn3k5-PvAA2LUmqGHVZ~XzGq~ILw) - Here we talk about research, architecture, and future development.
- [Discord server](https://discord.gg/ESHStjSjD4) - This is a community-run server for general discussion, questions, and feedback.

## 📈 Progress
<p align="center">
    <a href="https://www.swebench.com/lite.html">
        <img src="/docs/static/img/results.png" alt="SWE-Bench Lite Score" width="500" height="auto">
    </a>
</p>

<p align="center">
  <a href="https://star-history.com/#OpenDevin/OpenDevin&Date">
    <img src="https://api.star-history.com/svg?repos=OpenDevin/OpenDevin&type=Date" width="500" alt="Star History Chart">
  </a>
</p>

## 📜 License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.

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
