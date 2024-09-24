<div align="center">
  <img src="https://github.com/All-Hands-AI/OpenHands/raw/main/docs/static/img/logo.png" alt="OpenHands Banner" width="30%">

  # OpenHands: Code Less, Make More

  [![Contributors](https://img.shields.io/github/contributors/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)](https://github.com/All-Hands-AI/OpenHands/graphs/contributors)
  [![Stars](https://img.shields.io/github/stars/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)](https://github.com/All-Hands-AI/OpenHands/stargazers)
  [![Coverage](https://img.shields.io/codecov/c/github/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)](https://codecov.io/github/All-Hands-AI/OpenHands?branch=main)
  [![License](https://img.shields.io/github/license/All-Hands-AI/OpenHands?style=for-the-badge&color=blue)](https://github.com/All-Hands-AI/OpenHands/blob/main/LICENSE)

  [![Slack](https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge)](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA)
  [![Discord](https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/ESHStjSjD4)
  [![Documentation](https://img.shields.io/badge/Documentation-000?logo=googledocs&logoColor=FFE165&style=for-the-badge)](https://docs.all-hands.dev/modules/usage/getting-started)
  [![Paper](https://img.shields.io/badge/Paper%20on%20Arxiv-000?logoColor=FFE165&logo=arxiv&style=for-the-badge)](https://arxiv.org/abs/2407.16741)
  [![Benchmark](https://img.shields.io/badge/Benchmark%20score-000?logoColor=FFE165&logo=huggingface&style=for-the-badge)](https://huggingface.co/spaces/OpenHands/evaluation)
</div>

## 🚀 Table of Contents

- [About OpenHands](#-about-openhands)
- [Key Features](#-key-features)
- [Demo](#-demo)
- [Getting Started](#-getting-started)
- [Documentation](#-documentation)
- [Roadmap](#-roadmap)
- [How to Contribute](#-how-to-contribute)
- [Community](#-community)
- [FAQ](#-faq)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)
- [Cite](#-cite)

## 🤖 About OpenHands

OpenHands (formerly OpenDevin) is a cutting-edge platform for software development agents powered by AI. Our agents can perform any task a human developer can, including modifying code, running commands, browsing the web, and even copying code snippets from StackOverflow.

## ✨ Key Features

<div align="center">

| 🧠 AI-Powered Agents | 🌐 Web Integration | 🔧 Code Modification | 📚 Comprehensive Docs |
|:-------------------:|:-------------------:|:--------------------:|:---------------------:|
| Intelligent software development assistants | Seamless browsing and API capabilities | Effortless code updates and command execution | Detailed guides and community support |

</div>

## 🎥 Demo

| OpenHands Introduction | OpenHands Demo |
|:----------|:-----|
|[![OpenHands Introduction](http://img.youtube.com/vi/Q3DyeIV96tY/0.jpg)](https://www.youtube.com/watch?v=Q3DyeIV96tY) | [![OpenHands Demo](http://img.youtube.com/vi/2_6-ejOhHXQ/0.jpg)](https://www.youtube.com/watch?v=2_6-ejOhHXQ) |






## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/All-Hands-AI/OpenHands.git
   cd OpenHands
   ```

2. **Set up your workspace:**
   ```bash
   export WORKSPACE_BASE=$(pwd)/workspace
   ```

3. **Run OpenHands with Docker:**
   ```bash
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

4. **Access OpenHands:**
   Open your browser and visit [http://localhost:3000](http://localhost:3000)

## 📖 Documentation

For detailed information, setup instructions, and advanced configuration options, visit our [comprehensive documentation](https://docs.all-hands.dev/modules/usage/getting-started).

## 🗺️ Roadmap

- [ ] Enhanced natural language understanding
- [ ] Multi-agent collaboration features
- [ ] Expanded language and framework support
- [ ] Improved code generation capabilities
- [ ] Integration with popular IDEs

## 🤝 How to Contribute

We welcome contributions from everyone! Here's how you can get involved:

- 💻 **Code Contributions:** Help us develop new features and fix bugs
- 🔬 **Research and Evaluation:** Contribute to our understanding of AI in software engineering
- 🐛 **Feedback and Testing:** Use OpenHands and report issues or suggest improvements

Check out our [CONTRIBUTING.md](./CONTRIBUTING.md) for more details.

## 🌟 Community

Join our vibrant community and help shape the future of AI-assisted software development:

- 💬 [Slack Workspace](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA) - For research, architecture, and development discussions
- 🎮 [Discord Server](https://discord.gg/ESHStjSjD4) - For general discussion, questions, and feedback

## ❓ FAQ

<details>
<summary>What makes OpenHands different from other AI coding assistants?</summary>
OpenHands provides a complete platform for AI-powered software development, offering not just code suggestions, but full task automation and web integration capabilities.
</details>

<details>
<summary>Is OpenHands free to use?</summary>
Yes, OpenHands is open-source and free to use under the MIT License.
</details>

<details>
<summary>How can I contribute to the project?</summary>
Check out our [CONTRIBUTING.md](./CONTRIBUTING.md) file for guidelines on how to contribute code, research, or provide feedback.
</details>

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
