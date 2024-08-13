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
  <a href="https://github.com/All-Hands-AI/OpenHands/graphs/contributors"><img src="https://img.shields.io/github/contributors/openhands/openhands?style=for-the-badge&color=blue" alt="Contributors"></a>
  <a href="https://github.com/All-Hands-AI/OpenHands/network/members"><img src="https://img.shields.io/github/forks/openhands/openhands?style=for-the-badge&color=blue" alt="Forks"></a>
  <a href="https://github.com/All-Hands-AI/OpenHands/stargazers"><img src="https://img.shields.io/github/stars/openhands/openhands?style=for-the-badge&color=blue" alt="Stargazers"></a>
  <a href="https://github.com/All-Hands-AI/OpenHands/issues"><img src="https://img.shields.io/github/issues/openhands/openhands?style=for-the-badge&color=blue" alt="Issues"></a>
  <a href="https://github.com/All-Hands-AI/OpenHands/blob/main/LICENSE"><img src="https://img.shields.io/github/license/openhands/openhands?style=for-the-badge&color=blue" alt="MIT License"></a>
  <br/>
  <a href="https://join.slack.com/t/openhands/shared_invite/zt-2ngejmfw6-9gW4APWOC9XUp1n~SiQ6iw"><img src="https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge" alt="Join our Slack community"></a>
  <a href="https://discord.gg/ESHStjSjD4"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community"></a>
  <a href="https://codecov.io/github/openhands/openhands?branch=main"><img alt="CodeCov" src="https://img.shields.io/codecov/c/github/openhands/openhands?style=for-the-badge"></a>
</div>

<!-- PROJECT LOGO -->
<div align="center">
  <img src="./docs/static/img/logo.png" alt="Logo" width="200" height="200">
  <h1 align="center">Open Hands: Code Less, Make More</h1>
  <a href="https://docs.all-hands.dev/modules/usage/intro"><img src="https://img.shields.io/badge/Documentation-Open Hands-blue?logo=googledocs&logoColor=white&style=for-the-badge" alt="Check out the documentation"></a>
  <a href="https://arxiv.org/abs/2407.16741"><img src="https://img.shields.io/badge/Paper-%20on%20Arxiv-red?logo=arxiv&style=for-the-badge" alt="Paper on Arxiv"></a>
  <br/>
  <a href="https://huggingface.co/spaces/Open Hands/evaluation"><img src="https://img.shields.io/badge/Evaluation-Benchmark%20on%20HF%20Space-green?logo=huggingface&style=for-the-badge" alt="Evaluation Benchmark"></a>
</div>
<hr>

Welcome to Open Hands, a platform for autonomous software engineers, powered by AI and LLMs.

Open Hands agents collaborate with human developers to write code, fix bugs, and ship features.

![App screenshot](./docs/static/img/screenshot.png)

## ⚡ Getting Started
Open Hands works best with Docker version 26.0.0+ (Docker Desktop 4.31.0+).
You must be using Linux, Mac OS, or WSL on Windows.

To start Open Hands in a docker container, run the following commands in your terminal:

> [!WARNING]
> When you run the following command, files in `./workspace` may be modified or deleted.

```bash
WORKSPACE_BASE=$(pwd)/workspace
docker run -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/openhands/openhands:0.8
```

> [!NOTE]
> By default, this command pulls the `latest` tag, which represents the most recent release of Open Hands. You have other options as well:
> - For a specific release version, use `ghcr.io/openhands/openhands:<Open Hands_version>` (replace <Open Hands_version> with the desired version number).
> - For the most up-to-date development version, use `ghcr.io/openhands/openhands:main`. This version may be **(unstable!)** and is recommended for testing or development purposes only.
>
> Choose the tag that best suits your needs based on stability requirements and desired features.

You'll find Open Hands running at [http://localhost:3000](http://localhost:3000) with access to `./workspace`. To have Open Hands operate on your code, place it in `./workspace`.
Open Hands will only have access to this workspace folder. The rest of your system will not be affected as it runs in a secured docker sandbox.

Upon opening Open Hands, you must select the appropriate `Model` and enter the `API Key` within the settings that should pop up automatically. These can be set at any time by selecting
the `Settings` button (gear icon) in the UI. If the required `Model` does not exist in the list, you can manually enter it in the text box.

For the development workflow, see [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

Are you having trouble? Check out our [Troubleshooting Guide](https://docs.all-hands.dev/modules/usage/troubleshooting).

## 🚀 Documentation

To learn more about the project, and for tips on using Open Hands,
**check out our [documentation](https://docs.all-hands.dev/modules/usage/intro)**.

There you'll find resources on how to use different LLM providers (like ollama and Anthropic's Claude),
troubleshooting resources, and advanced configuration options.

## 🤝 How to Contribute

Open Hands is a community-driven project, and we welcome contributions from everyone.
Whether you're a developer, a researcher, or simply enthusiastic about advancing the field of
software engineering with AI, there are many ways to get involved:

- **Code Contributions:** Help us develop new agents, core functionality, the frontend and other interfaces, or sandboxing solutions.
- **Research and Evaluation:** Contribute to our understanding of LLMs in software engineering, participate in evaluating the models, or suggest improvements.
- **Feedback and Testing:** Use the Open Hands toolset, report bugs, suggest features, or provide feedback on usability.

For details, please check [CONTRIBUTING.md](./CONTRIBUTING.md).

## 🤖 Join Our Community

Whether you're a developer, a researcher, or simply enthusiastic about Open Hands, we'd love to have you in our community.
Let's make software engineering better together!

- [Slack workspace](https://join.slack.com/t/openhands/shared_invite/zt-2ngejmfw6-9gW4APWOC9XUp1n~SiQ6iw) - Here we talk about research, architecture, and future development.
- [Discord server](https://discord.gg/ESHStjSjD4) - This is a community-run server for general discussion, questions, and feedback.

## 📈 Progress

<p align="center">
  <a href="https://star-history.com/#Open Hands/Open Hands&Date">
    <img src="https://api.star-history.com/svg?repos=Open Hands/Open Hands&type=Date" width="500" alt="Star History Chart">
  </a>
</p>

## 📜 License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.

[contributors-shield]: https://img.shields.io/github/contributors/openhands/openhands?style=for-the-badge
[contributors-url]: https://github.com/All-Hands-AI/OpenHands/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/openhands/openhands?style=for-the-badge
[forks-url]: https://github.com/All-Hands-AI/OpenHands/network/members
[stars-shield]: https://img.shields.io/github/stars/openhands/openhands?style=for-the-badge
[stars-url]: https://github.com/All-Hands-AI/OpenHands/stargazers
[issues-shield]: https://img.shields.io/github/issues/openhands/openhands?style=for-the-badge
[issues-url]: https://github.com/All-Hands-AI/OpenHands/issues
[license-shield]: https://img.shields.io/github/license/openhands/openhands?style=for-the-badge
[license-url]: https://github.com/All-Hands-AI/OpenHands/blob/main/LICENSE

## 📚 Cite

```
@misc{openhands,
      title={{Open Hands: An Open Platform for AI Software Developers as Generalist Agents}},
      author={Xingyao Wang and Boxuan Li and Yufan Song and Frank F. Xu and Xiangru Tang and Mingchen Zhuge and Jiayi Pan and Yueqi Song and Bowen Li and Jaskirat Singh and Hoang H. Tran and Fuqiang Li and Ren Ma and Mingzhang Zheng and Bill Qian and Yanjun Shao and Niklas Muennighoff and Yizhe Zhang and Binyuan Hui and Junyang Lin and Robert Brennan and Hao Peng and Heng Ji and Graham Neubig},
      year={2024},
      eprint={2407.16741},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2407.16741},
}
```
