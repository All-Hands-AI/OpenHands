<div align="center">

  ![OpenHands Logo](./docs/static/img/logo.png)

  # OpenHands: Code Less, Make More

  ![Contributors](https://img.shields.io/github/contributors/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)
  ![Stars](https://img.shields.io/github/stars/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)
  ![Coverage](https://img.shields.io/codecov/c/github/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)
  ![License](https://img.shields.io/github/license/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)

  [![Slack](https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge)](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA)
  [![Discord](https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/ESHStjSjD4)
  [![Credits](https://img.shields.io/badge/Project-Credits-blue?style=for-the-badge&color=FFE165&logo=github&logoColor=white)](https://github.com/All-Hands-AI/OpenHands/blob/main/CREDITS.md)

  [![Docs](https://img.shields.io/badge/Documentation-000?logo=googledocs&logoColor=FFE165&style=for-the-badge)](https://docs.all-hands.dev/modules/usage/getting-started)
  [![Paper](https://img.shields.io/badge/Paper%20on%20Arxiv-000?logoColor=FFE165&logo=arxiv&style=for-the-badge)](https://arxiv.org/abs/2407.16741)
  [![Benchmark](https://img.shields.io/badge/Benchmark%20score-000?logoColor=FFE165&logo=huggingface&style=for-the-badge)](https://huggingface.co/spaces/OpenHands/evaluation)

</div>

<p align="center">
  <img src="./docs/static/img/screenshot.png" alt="OpenHands Screenshot" width="600">
</p>

## 🚀 Table of Contents

- [About OpenHands](#-about-openhands)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
- [How to Contribute](#-how-to-contribute)
- [Join Our Community](#-join-our-community)
- [Progress](#-progress)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)
- [Cite](#-cite)

## 🤖 About OpenHands

OpenHands (formerly OpenDevin) is a cutting-edge platform for software development agents powered by AI. Our agents can perform any task a human developer can, including modifying code, running commands, browsing the web, and even copying code snippets from StackOverflow.

## ✨ Features

- 🧠 AI-powered software development agents
- 🌐 Web browsing and API integration capabilities
- 🔧 Code modification and command execution
- 📚 Comprehensive documentation and community support
- 🔬 Ongoing research and evaluation

## ⚡ Quick Start

<details>
<summary>Click to expand Quick Start guide</summary>

The easiest way to run OpenHands is in Docker. Change `WORKSPACE_BASE` to point OpenHands to existing code you'd like to modify.

```bash
export WORKSPACE_BASE=$(pwd)/workspace

docker run -it --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.9-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/all-hands-ai/openhands:0.9
```

Visit [http://localhost:3000](http://localhost:3000) to start using OpenHands!

</details>

## 📖 Documentation

For detailed information, setup instructions, and advanced configuration options, visit our [comprehensive documentation](https://docs.all-hands.dev/modules/usage/getting-started).

## 🤝 How to Contribute

We welcome contributions from everyone! Whether you're a developer, researcher, or enthusiast, there are many ways to get involved:

- 💻 Code Contributions
- 🔬 Research and Evaluation
- 🐛 Feedback and Testing

Check out our [CONTRIBUTING.md](./CONTRIBUTING.md) for more details.

## 🌟 Join Our Community

Let's revolutionize software engineering together!

- 💬 [Slack Workspace](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA) - For research, architecture, and development discussions
- 🎮 [Discord Server](https://discord.gg/ESHStjSjD4) - For general discussion, questions, and feedback

## 📈 Progress

<p align="center">
  <a href="https://star-history.com/#All-Hands-AI/OpenHands&Date">
    <img src="https://api.star-history.com/svg?repos=All-Hands-AI/OpenHands&type=Date" alt="Star History Chart" width="500">
  </a>
</p>

## 📜 License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.

## 🙏 Acknowledgements

OpenHands is built by a large number of contributors. We're deeply thankful for their work and the open-source projects we build upon. See [CREDITS.md](./CREDITS.md) for a full list.

## 📚 Cite

```bibtex
@misc{opendevin,
      title={{OpenDevin: An Open Platform for AI Software Developers as Generalist Agents}},
      author={Xingyao Wang and Boxuan Li and Yufan Song and Frank F. Xu and Xiangru Tang and Mingchen Zhuge and Jiayi Pan and Yueqi Song and Bowen Li and Jaskirat Singh and Hoang H. Tran and Fuqiang Li and Ren Ma and Mingzhang Zheng and Bill Qian and Yanjun Shao and Niklas Muennighoff and Yizhe Zhang and Binyuan Hui and Junyang Lin and Robert Brennan and Hao Peng and Heng Ji and Graham Neubig},
      year={2024},
      eprint={2407.16741},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2407.16741},
}
```

<div align="center">

  Made with ❤️ by the OpenHands Community

</div>
