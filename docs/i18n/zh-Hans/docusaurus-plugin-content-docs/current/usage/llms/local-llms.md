# 使用SGLang或vLLM的本地LLM

:::warning
使用本地LLM时，OpenHands可能功能有限。
强烈建议您使用GPU来提供本地模型服务，以获得最佳体验。
:::

## 新闻

- 2025/03/31：我们发布了开源模型OpenHands LM v0.1 32B，在SWE-Bench Verified上达到37.1%的成绩
（[博客](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model)，[模型](https://huggingface.co/all-hands/openhands-lm-32b-v0.1)）。

## 从Huggingface下载模型

例如，要下载[OpenHands LM 32B v0.1](https://huggingface.co/all-hands/openhands-lm-32b-v0.1)：

```bash
huggingface-cli download all-hands/openhands-lm-32b-v0.1 --local-dir all-hands/openhands-lm-32b-v0.1
```

## 使用模型服务框架创建兼容OpenAI的端点

### 使用SGLang提供服务

- 按照[官方文档](https://docs.sglang.ai/start/install.html)安装SGLang。
- OpenHands LM 32B的示例启动命令（至少需要2个GPU）：

```bash
SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 python3 -m sglang.launch_server \
    --model all-hands/openhands-lm-32b-v0.1 \
    --served-model-name openhands-lm-32b-v0.1 \
    --port 8000 \
    --tp 2 --dp 1 \
    --host 0.0.0.0 \
    --api-key mykey --context-length 131072
```

### 使用vLLM提供服务

- 按照[官方文档](https://docs.vllm.ai/en/latest/getting_started/installation.html)安装vLLM。
- OpenHands LM 32B的示例启动命令（至少需要2个GPU）：

```bash
vllm serve all-hands/openhands-lm-32b-v0.1 \
    --host 0.0.0.0 --port 8000 \
    --api-key mykey \
    --tensor-parallel-size 2 \
    --served-model-name openhands-lm-32b-v0.1
    --enable-prefix-caching
```

## 运行和配置OpenHands

### 运行OpenHands

#### 使用Docker

使用[官方docker运行命令](../installation#start-the-app)运行OpenHands。

#### 使用开发模式

使用[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)中的说明构建OpenHands。
通过运行`make setup-config`确保`config.toml`存在，它会为您创建一个。在`config.toml`中，输入以下内容：

```
[core]
workspace_base="/path/to/your/workspace"

[llm]
model="openhands-lm-32b-v0.1"
ollama_base_url="http://localhost:8000"
```

使用`make run`启动OpenHands。

### 配置OpenHands

一旦OpenHands运行起来，您需要通过设置在OpenHands UI中设置以下内容：
1. 启用`高级`选项。
2. 设置以下内容：
- `自定义模型`为`openai/<served-model-name>`（例如`openai/openhands-lm-32b-v0.1`）
- `基础URL`为`http://host.docker.internal:8000`
- `API密钥`为您在提供模型服务时设置的相同字符串（例如`mykey`）
