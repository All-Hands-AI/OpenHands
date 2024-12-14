以下是翻译后的内容:

# 🚧 故障排除

有一些错误信息经常被用户报告。我们会尽量让安装过程更简单,但目前您可以在下面查找您的错误信息,看看是否有任何解决方法。如果您找到了更多关于这些问题的信息或解决方法,请提交一个 *PR* 来添加详细信息到这个文件。

:::tip
OpenHands 仅通过 [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) 支持 Windows。
请确保在您的 WSL 终端内运行所有命令。
:::

## 常见问题

* [无法连接到 Docker](#unable-to-connect-to-docker)
* [404 资源未找到](#404-resource-not-found)
* [`make build` 在安装包时卡住](#make-build-getting-stuck-on-package-installations)
* [会话没有恢复](#sessions-are-not-restored)

### 无法连接到 Docker

[GitHub Issue](https://github.com/All-Hands-AI/OpenHands/issues/1226)

**症状**

```bash
Error creating controller. Please check Docker is running and visit `https://docs.all-hands.dev/modules/usage/troubleshooting` for more debugging information.
```

```bash
docker.errors.DockerException: Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

**详情**

OpenHands 使用 Docker 容器来安全地工作,而不会潜在地破坏您的机器。

**解决方法**

* 运行 `docker ps` 以确保 docker 正在运行
* 确保您不需要 `sudo` 来运行 docker [参见此处](https://www.baeldung.com/linux/docker-run-without-sudo)
* 如果您在 Mac 上,请检查 [权限要求](https://docs.docker.com/desktop/mac/permission-requirements/),特别是考虑在 Docker Desktop 的 `Settings > Advanced` 下启用 `Allow the default Docker socket to be used`。
* 此外,在 `Check for Updates` 下将您的 Docker 升级到最新版本

---
### `404 资源未找到`

**症状**

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

**详情**

当 LiteLLM(我们用于连接不同 LLM 提供商的库)找不到您尝试连接的 API 端点时,就会发生这种情况。这种情况最常发生在 Azure 或 ollama 用户身上。

**解决方法**

* 检查您是否正确设置了 `LLM_BASE_URL`
* 根据 [LiteLLM 文档](https://docs.litellm.ai/docs/providers) 检查模型是否设置正确
  * 如果您在 UI 内运行,请确保在设置模态框中设置 `model`
  * 如果您在无头模式下运行(通过 main.py),请确保在您的 env/config 中设置 `LLM_MODEL`
* 确保您已遵循 LLM 提供商的任何特殊说明
  * [Azure](/modules/usage/llms/azure-llms)
  * [Google](/modules/usage/llms/google-llms)
* 确保您的 API 密钥正确
* 看看您是否可以使用 `curl` 连接到 LLM
* 尝试 [直接通过 LiteLLM 连接](https://github.com/BerriAI/litellm) 以测试您的设置

---
### `make build` 在安装包时卡住

**症状**

包安装在 `Pending...` 处卡住,没有任何错误信息:

```bash
Package operations: 286 installs, 0 updates, 0 removals

  - Installing certifi (2024.2.2): Pending...
  - Installing h11 (0.14.0): Pending...
  - Installing idna (3.7): Pending...
  - Installing sniffio (1.3.1): Pending...
  - Installing typing-extensions (4.11.0): Pending...
```

**详情**

在极少数情况下,`make build` 可能会在安装包时看似卡住,没有任何错误信息。

**解决方法**

包安装程序 Poetry 可能缺少一个配置设置,用于查找凭据的位置(keyring)。

首先用 `env` 检查是否存在 `PYTHON_KEYRING_BACKEND` 的值。
如果没有,运行下面的命令将其设置为一个已知值,然后重试构建:

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

---
### 会话没有恢复

**症状**

OpenHands 通常在打开 UI 时询问是恢复还是开始新会话。
但是点击"恢复"仍然会开始一个全新的聊天。

**详情**

截至目前,使用标准安装,会话数据存储在内存中。
目前,如果 OpenHands 的服务重新启动,之前的会话会变得无效(生成一个新的密钥),因此无法恢复。

**解决方法**

* 通过编辑 `config.toml` 文件(在 OpenHands 的根文件夹中)来更改配置,使会话持久化,指定一个 `file_store` 和一个绝对的 `file_store_path`:

```toml
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
```

* 在您的 .bashrc 中添加一个固定的 jwt 密钥,如下所示,这样之前的会话 id 应该可以保持被接受。

```bash
EXPORT JWT_SECRET=A_CONST_VALUE
```
