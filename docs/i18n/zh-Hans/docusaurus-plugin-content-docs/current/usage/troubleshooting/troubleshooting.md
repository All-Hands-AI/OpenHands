---
sidebar_position: 5
---

# 🚧 故障排除

以下是用户经常报告的一些错误信息。

我们将努力使安装过程更加简单，并改善这些错误信息。不过，现在您可以在下面找到您的错误信息，并查看是否有任何解决方法。

对于这些错误信息，**都已经有相关的报告**。请不要打开新的报告——只需在现有的报告中发表评论即可。

如果您发现更多信息或者一个解决方法，请提交一个 *PR* 来添加细节到这个文件中。

:::tip
如果您在 Windows 上运行并遇到问题，请查看我们的[Windows (WSL) 用户指南](troubleshooting/windows)。
:::

## 无法连接到 Docker

[GitHub 问题](https://github.com/All-Hands-AI/OpenHands/issues/1226)

### 症状

```bash
创建控制器时出错。请检查 Docker 是否正在运行，并访问 `https://docs.all-hands.dev/modules/usage/troubleshooting` 获取更多调试信息。
```

```bash
docker.errors.DockerException: 获取服务器 API 版本时出错: ('连接中止。', FileNotFoundError(2, '没有这样的文件或目录'))
```

### 详情

OpenHands 使用 Docker 容器来安全地完成工作，而不会破坏您的机器。

### 解决方法

* 运行 `docker ps` 以确保 Docker 正在运行
* 确保您不需要使用 `sudo` 运行 Docker [请参见此处](https://www.baeldung.com/linux/docker-run-without-sudo)
* 如果您使用的是 Mac，请检查[权限要求](https://docs.docker.com/desktop/mac/permission-requirements/) ，特别是考虑在 Docker Desktop 的 `Settings > Advanced` 下启用 `Allow the default Docker socket to be used`。
* 另外，升级您的 Docker 到最新版本，选择 `Check for Updates`

## 无法连接到 DockerSSHBox

[GitHub 问题](https://github.com/All-Hands-AI/OpenHands/issues/1156)

### 症状

```python
self.shell = DockerSSHBox(
...
pexpect.pxssh.ExceptionPxssh: Could not establish connection to host
```

### 详情

默认情况下，OpenHands 使用 SSH 连接到一个运行中的容器。在某些机器上，尤其是 Windows，这似乎会失败。

### 解决方法

* 重新启动您的计算机（有时会有用）
* 确保拥有最新版本的 WSL 和 Docker
* 检查您的 WSL 分发版也已更新
* 尝试[此重新安装指南](https://github.com/All-Hands-AI/OpenHands/issues/1156#issuecomment-2064549427)

## 无法连接到 LLM

[GitHub 问题](https://github.com/All-Hands-AI/OpenHands/issues/1208)

### 症状

```python
  File "/app/.venv/lib/python3.12/site-packages/openai/_exceptions.py", line 81, in __init__
    super().__init__(message, response.request, body=body)
                              ^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'request'
```

### 详情

[GitHub 问题](https://github.com/All-Hands-AI/OpenHands/issues?q=is%3Aissue+is%3Aopen+404)

这通常发生在本地 LLM 设置中，当 OpenHands 无法连接到 LLM 服务器时。请参阅我们的 [本地 LLM 指南](llms/local-llms) 以获取更多信息。

### 解决方法

* 检查您的 `config.toml` 文件中 "llm" 部分的 `base_url` 是否正确（如果存在）
* 检查 Ollama（或您使用的其他 LLM）是否正常运行
* 确保在 Docker 中运行时使用 `--add-host host.docker.internal:host-gateway`

## `404 Resource not found 资源未找到`

### 症状

```python
Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 414, in completion
    raise e
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 373, in completion
    response = openai_client.chat.completions.create(**data, timeout=timeout)  # type: ignore
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_utils/_utils.py", line 277, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/resources/chat/completions.py", line 579, in create
    return self._post(
           ^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1232, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 921, in request
    return self._request(
           ^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1012, in _request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
```

### 详情

当 LiteLLM（我们用于连接不同 LLM 提供商的库）找不到您要连接的 API 端点时，会发生这种情况。最常见的情况是 Azure 或 Ollama 用户。

### 解决方法

* 检查您是否正确设置了 `LLM_BASE_URL`
* 检查模型是否正确设置，基于 [LiteLLM 文档](https://docs.litellm.ai/docs/providers)
  * 如果您在 UI 中运行，请确保在设置模式中设置 `model`
  * 如果您通过 main.py 运行，请确保在环境变量/配置中设置 `LLM_MODEL`
* 确保遵循了您的 LLM 提供商的任何特殊说明
  * [Ollama](/zh-Hans/modules/usage/llms/local-llms)
  * [Azure](/zh-Hans/modules/usage/llms/azure-llms)
  * [Google](/zh-Hans/modules/usage/llms/google-llms)
* 确保您的 API 密钥正确无误
* 尝试使用 `curl` 连接到 LLM
* 尝试[直接通过 LiteLLM 连接](https://github.com/BerriAI/litellm)来测试您的设置

## `make build` 在安装包时卡住

### 症状

安装包时卡在 `Pending...`，没有任何错误信息：

```bash
Package operations: 286 installs, 0 updates, 0 removals

  - Installing certifi (2024.2.2): Pending...
  - Installing h11 (0.14.0): Pending...
  - Installing idna (3.7): Pending...
  - Installing sniffio (1.3.1): Pending...
  - Installing typing-extensions (4.11.0): Pending...
```

### 详情

在极少数情况下，`make build` 在安装包时似乎会卡住，没有任何错误信息。

### 解决方法

* 包管理器 Poetry 可能会错过用于查找凭据的配置设置（keyring）。

### 解决方法

首先使用 `env` 检查是否存在 `PYTHON_KEYRING_BACKEND` 的值。如果不存在，运行以下命令将其设置为已知值，然后重试构建：

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

## 会话未恢复

### 症状

通常情况下，当打开 UI 时，OpenHands 会询问是否要恢复或开始新会话。但点击“恢复”仍然会开始一个全新的聊天。

### 详情

按今天的标准安装，会话数据存储在内存中。目前，如果 OpenHands 的服务重启，以前的会话将失效（生成一个新秘密），因此无法恢复。

### 解决方法

* 通过编辑 OpenHands 根文件夹中的 `config.toml` 文件，更改配置以使会话持久化，指定一个 `file_store` 和一个绝对路径的 `file_store_path`：

```toml
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
```

* 在您的 .bashrc 中添加一个固定的 JWT 秘密，如下所示，以便以前的会话 ID 可以被接受。

```bash
EXPORT JWT_SECRET=A_CONST_VALUE
```
