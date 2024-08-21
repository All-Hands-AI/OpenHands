# 💿 如何创建自定义 Docker 沙箱

默认的 OpenHands 沙箱包含一个[最小化 ubuntu 配置](https://github.com/All-Hands-AI/OpenHands/blob/main/containers/sandbox/Dockerfile)。您的应用场景可能需要在默认状态下安装额外的软件。本指南将教您如何通过使用自定义 Docker 映像来实现这一目标。

## 环境设置

确保您能够首先通过 [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) 运行 OpenHands。

## 创建您的 Docker 映像

接下来，您必须创建一个自定义的 Docker 映像，该映像是基于 Debian 或 Ubuntu 的。例如，如果我们希望 OpenHands 能够访问 "node" 可执行文件，我们可以使用以下 `Dockerfile`:

```bash
# 从最新版 ubuntu 开始
FROM ubuntu:latest

# 运行必要的更新
RUN apt-get update && apt-get install

# 安装 node
RUN apt-get install -y nodejs
```

然后构建您选择的映像，例如“custom_image”。为此可以在目录中创建文件夹并将 `Dockerfile` 放入其中，并在该目录内运行以下命令：

```bash
docker build -t custom_image .
```

这将生成一个名为 ```custom_image``` 的新映像，并使其可用于 Docker 服务引擎。

> 注意：在本文档描述的配置中，OpenHands 将在沙箱内部以“openhands”用户身份运行。因此，通过 Dockerfile 安装的所有包应可供系统上的所有用户使用，而不仅仅是 root 用户。

> 使用 `apt-get` 上面安装的 node 是为所有用户安装的。

## 在 config.toml 文件中指定自定义映像

在 OpenHands 的配置通过顶层的 `config.toml` 文件发生。在 OpenHands 目录下创建一个 ```config.toml``` 文件，并输入以下内容：

```
[core]
workspace_base="./workspace"
run_as_openhands=true
sandbox_container_image="custom_image"
```

> 确保 `sandbox_container_image` 设置为您前一步中自定义映像的名称。

## 运行

通过运行 ```make run``` 在顶层目录下运行 OpenHands。

导航至 ```localhost:3001``` 并检查所需依赖是否可用。

在上述示例的情况下，终端中运行 `node -v` 会输出 `v18.19.1`。

恭喜您！

## 技术解释

相关代码定义在 [ssh_box.py](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/ssh_box.py) 和 [image_agnostic_util.py](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/image_agnostic_util.py) 中。

特别是 ssh_box.py 检查配置对象中的 ```config.sandbox_container_image```，然后尝试使用 [get_od_sandbox_image](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/image_agnostic_util.py#L72)，在 image_agnostic_util.py 定义中进行检索。

初次使用自定义映像时，该映像将不会被找到，因此将被构建（在后续运行中已构建的映像将被查找并返回）。

自定义映像是通过 `_build_sandbox_image()` 构建的，在 [image_agnostic_util.py](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/image_agnostic_util.py#L29) 中，使用您的 custom_image 作为基础，并为 OpenHands 配置环境。例如：

```python
dockerfile_content = (
        f'FROM {base_image}\n'
        'RUN apt update && apt install -y openssh-server wget sudo\n'
        'RUN mkdir -p -m0755 /var/run/sshd\n'
        'RUN mkdir -p /openhands && mkdir -p /openhands/logs && chmod 777 /openhands/logs\n'
        'RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"\n'
        'RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /openhands/miniforge3\n'
        'RUN bash -c ". /openhands/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"\n'
        'RUN echo "export PATH=/openhands/miniforge3/bin:$PATH" >> ~/.bashrc\n'
        'RUN echo "export PATH=/openhands/miniforge3/bin:$PATH" >> /openhands/bash.bashrc\n'
    ).strip()
```

> 注意：映像名称通过 [_get_new_image_name()](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/image_agnostic_util.py#L63) 修改，并且是后续运行中搜索的修改后的名称。

## 故障排除 / 错误

### 错误：```useradd: UID 1000 is not unique```

如果在控制台输出中看到此错误，说明 OpenHands 尝试在沙箱中以 UID 1000 创建 openhands 用户，但该 UID 已经被映像中的其他部分使用（不知何故）。要解决这个问题，请更改 config.toml 文件中的 sandbox_user_id 字段为不同的值：

```
[core]
workspace_base="./workspace"
run_as_openhands=true
sandbox_container_image="custom_image"
sandbox_user_id="1001"
```

### 端口使用错误

如果您看到关于端口被占用或不可用的错误，请尝试删除所有正在运行的 Docker 容器（通过运行 `docker ps` 和 `docker rm` 相关容器），然后重新运行 ```make run```。

## 讨论

对于其他问题或疑问，请加入 [Slack](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA) 或 [Discord](https://discord.gg/ESHStjSjD4)，并提问！
