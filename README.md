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
  <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2i1iqdag6-bVmvamiPA9EZUu7oCO6KhA"><img src="https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge" alt="Join our Slack community"></a>
  <a href="https://discord.gg/ESHStjSjD4"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community"></a>
</div>

<!-- PROJECT LOGO -->
<div align="center">
  <img src="./docs/static/img/logo.png" alt="Logo" width="200" height="200">
  <h1 align="center">OpenDevin: Code Less, Make More</h1>
  <a href="https://opendevin.github.io/OpenDevin/"><img src="https://img.shields.io/badge/Documenation-OpenDevin-blue?logo=googledocs&logoColor=white&style=for-the-badge" alt="Check out the documentation"></a>
</div>

## 🎯 Mission

Welcome to OpenDevin, an open-source project aiming to replicate Devin, an autonomous AI software engineer who is capable of executing complex engineering tasks and collaborating actively with users on software development projects. This project aspires to replicate, enhance, and innovate upon Devin through the power of the open-source community.

## [🚀 Get Started](https://opendevin.github.io/OpenDevin/modules/usage/intro)

To learn more and to use OpenDevin, **check out our [documentation](https://opendevin.github.io/OpenDevin/)**!

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## ⚡ Quick Start
You can run OpenDevin with Docker. It works best with the most recent
version of Docker, `26.0.0`.

```bash
#The directory you want OpenDevin to modify. MUST be an absolute path!
export WORKSPACE_BASE=$(pwd)/workspace;

docker run \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    ghcr.io/opendevin/opendevin:0.5
```

For troubleshooting and advanced configuration, see
[the full documentation](https://opendevin.github.io/OpenDevin/).

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

- [Slack workspace](https://join.slack.com/t/opendevin/shared_invite/zt-2ggtwn3k5-PvAA2LUmqGHVZ~XzGq~ILw)
- [Discord server](https://discord.gg/ESHStjSjD4)

If you would love to contribute, feel free to join our community (note that now there is no need to fill in the [form](https://forms.gle/758d5p6Ve8r2nxxq6)). Let's simplify software engineering together!

🐚 **Code less, make more with OpenDevin.**

[![Star History Chart](https://api.star-history.com/svg?repos=OpenDevin/OpenDevin&type=Date)](https://star-history.com/#OpenDevin/OpenDevin&Date)

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
