# 配置选项

本指南详细介绍了 OpenHands 的所有可用配置选项,帮助您自定义其行为并与其他服务集成。

:::note
如果您在 [GUI 模式](https://docs.all-hands.dev/modules/usage/how-to/gui-mode) 下运行,Settings UI 中的可用设置将始终优先。
:::

---

# 目录

1. [核心配置](#核心配置)
   - [API Keys](#api-keys)
   - [工作区](#工作区)
   - [调试和日志记录](#调试和日志记录)
   - [会话管理](#会话管理)
   - [轨迹](#轨迹)
   - [文件存储](#文件存储)
   - [任务管理](#任务管理)
   - [沙箱配置](#沙箱配置)
   - [其他](#其他)
2. [LLM 配置](#llm-配置)
   - [AWS 凭证](#aws-凭证)
   - [API 配置](#api-配置)
   - [自定义 LLM Provider](#自定义-llm-provider)
   - [Embeddings](#embeddings)
   - [消息处理](#消息处理)
   - [模型选择](#模型选择)
   - [重试](#重试)
   - [高级选项](#高级选项)
3. [Agent 配置](#agent-配置)
   - [Microagent 配置](#microagent-配置)
   - [内存配置](#内存配置)
   - [LLM 配置](#llm-配置-2)
   - [ActionSpace 配置](#actionspace-配置)
   - [Microagent 使用](#microagent-使用)
4. [沙箱配置](#沙箱配置-2)
   - [执行](#执行)
   - [容器镜像](#容器镜像)
   - [网络](#网络)
   - [Linting 和插件](#linting-和插件)
   - [依赖和环境](#依赖和环境)
   - [评估](#评估)
5. [安全配置](#安全配置)
   - [确认模式](#确认模式)
   - [安全分析器](#安全分析器)

---

## 核心配置

核心配置选项在 `config.toml` 文件的 `[core]` 部分中定义。

**API Keys**
- `e2b_api_key`
  - 类型: `str`
  - 默认值: `""`
  - 描述: E2B 的 API key

- `modal_api_token_id`
  - 类型: `str`
  - 默认值: `""`
  - 描述: Modal 的 API token ID

- `modal_api_token_secret`
  - 类型: `str`
  - 默认值: `""`
  - 描述: Modal 的 API token secret

**工作区**
- `workspace_base`
  - 类型: `str`
  - 默认值: `"./workspace"`
  - 描述: 工作区的基础路径

- `cache_dir`
  - 类型: `str`
  - 默认值: `"/tmp/cache"`
  - 描述: 缓存目录路径

**调试和日志记录**
- `debug`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 启用调试

- `disable_color`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 禁用终端输出中的颜色

**轨迹**
- `save_trajectory_path`
  - 类型: `str`
  - 默认值: `"./trajectories"`
  - 描述: 存储轨迹的路径(可以是文件夹或文件)。如果是文件夹,轨迹将保存在该文件夹中以会话 ID 命名的 .json 文件中。

**文件存储**
- `file_store_path`
  - 类型: `str`
  - 默认值: `"/tmp/file_store"`
  - 描述: 文件存储路径

- `file_store`
  - 类型: `str`
  - 默认值: `"memory"`
  - 描述: 文件存储类型

- `file_uploads_allowed_extensions`
  - 类型: `list of str`
  - 默认值: `[".*"]`
  - 描述: 允许上传的文件扩展名列表

- `file_uploads_max_file_size_mb`
  - 类型: `int`
  - 默认值: `0`
  - 描述: 上传文件的最大文件大小,以 MB 为单位

- `file_uploads_restrict_file_types`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 限制文件上传的文件类型

- `file_uploads_allowed_extensions`
  - 类型: `list of str`
  - 默认值: `[".*"]`
  - 描述: 允许上传的文件扩展名列表

**任务管理**
- `max_budget_per_task`
  - 类型: `float`
  - 默认值: `0.0`
  - 描述: 每个任务的最大预算(0.0 表示无限制)

- `max_iterations`
  - 类型: `int`
  - 默认值: `100`
  - 描述: 最大迭代次数

**沙箱配置**
- `workspace_mount_path_in_sandbox`
  - 类型: `str`
  - 默认值: `"/workspace"`
  - 描述: 在沙箱中挂载工作区的路径

- `workspace_mount_path`
  - 类型: `str`
  - 默认值: `""`
  - 描述: 挂载工作区的路径

- `workspace_mount_rewrite`
  - 类型: `str`
  - 默认值: `""`
  - 描述: 重写工作区挂载路径的路径。通常可以忽略这个,它指的是在另一个容器内运行的特殊情况。

**其他**
- `run_as_openhands`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 以 OpenHands 身份运行

- `runtime`
  - 类型: `str`
  - 默认值: `"eventstream"`
  - 描述: 运行时环境

- `default_agent`
  - 类型: `str`
  - 默认值: `"CodeActAgent"`
  - 描述: 默认 agent 的名称

- `jwt_secret`
  - 类型: `str`
  - 默认值: `uuid.uuid4().hex`
  - 描述: 用于身份验证的 JWT 密钥。请将其设置为您自己的值。

## LLM 配置

LLM(大语言模型)配置选项在 `config.toml` 文件的 `[llm]` 部分中定义。

要在 docker 命令中使用这些选项,请传入 `-e LLM_<option>`。例如: `-e LLM_NUM_RETRIES`。

**AWS 凭证**
- `aws_access_key_id`
  - 类型: `str`
  - 默认值: `""`
  - 描述: AWS access key ID

- `aws_region_name`
  - 类型: `str`
  - 默认值: `""`
  - 描述: AWS region name

- `aws_secret_access_key`
  - 类型: `str`
  - 默认值: `""`
  - 描述: AWS secret access key

**API 配置**
- `api_key`
  - 类型: `str`
  - 默认值: `None`
  - 描述: 要使用的 API key

- `base_url`
  - 类型: `str`
  - 默认值: `""`
  - 描述: API 基础 URL

- `api_version`
  - 类型: `str`
  - 默认值: `""`
  - 描述: API 版本

- `input_cost_per_token`
  - 类型: `float`
  - 默认值: `0.0`
  - 描述: 每个输入 token 的成本

- `output_cost_per_token`
  - 类型: `float`
  - 默认值: `0.0`
  - 描述: 每个输出 token 的成本

**自定义 LLM Provider**
- `custom_llm_provider`
  - 类型: `str`
  - 默认值: `""`
  - 描述: 自定义 LLM provider

**Embeddings**
- `embedding_base_url`
  - 类型: `str`
  - 默认值: `""`
  - 描述: Embedding API 基础 URL

- `embedding_deployment_name`
  - 类型: `str`
  - 默认值: `""`
  - 描述: Embedding 部署名称

- `embedding_model`
  - 类型: `str`
  - 默认值: `"local"`
  - 描述: 要使用的 Embedding 模型

**消息处理**
- `max_message_chars`
  - 类型: `int`
  - 默认值: `30000`
  - 描述: 包含在提示 LLM 的事件内容中的最大字符数(近似值)。较大的观察结果会被截断。

- `max_input_tokens`
  - 类型: `int`
  - 默认值: `0`
  - 描述: 最大输入 token 数

- `max_output_tokens`
  - 类型: `int`
  - 默认值: `0`
  - 描述: 最大输出 token 数

**模型选择**
- `model`
  - 类型: `str`
  - 默认值: `"claude-3-5-sonnet-20241022"`
  - 描述: 要使用的模型

**重试**
- `num_retries`
  - 类型: `int`
  - 默认值: `8`
  - 描述: 尝试重试的次数

- `retry_max_wait`
  - 类型: `int`
  - 默认值: `120`
  - 描述: 重试尝试之间的最大等待时间(秒)

- `retry_min_wait`
  - 类型: `int`
  - 默认值: `15`
  - 描述: 重试尝试之间的最小等待时间(秒)

- `retry_multiplier`
  - 类型: `float`
  - 默认值: `2.0`
  - 描述: 指数退避计算的乘数

**高级选项**
- `drop_params`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 丢弃任何未映射(不支持)的参数,而不会引发异常

- `caching_prompt`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 如果 LLM 提供并支持,则使用提示缓存功能

- `ollama_base_url`
  - 类型: `str`
  - 默认值: `""`
  - 描述: OLLAMA API 的基础 URL

- `temperature`
  - 类型: `float`
  - 默认值: `0.0`
  - 描述: API 的 temperature

- `timeout`
  - 类型: `int`
  - 默认值: `0`
  - 描述: API 的超时时间

- `top_p`
  - 类型: `float`
  - 默认值: `1.0`
  - 描述: API 的 top p

- `disable_vision`
  - 类型: `bool`
  - 默认值: `None`
  - 描述: 如果模型支持视觉,此选项允许禁用图像处理(对于降低成本很有用)

## Agent 配置

Agent 配置选项在 `config.toml` 文件的 `[agent]` 和 `[agent.<agent_name>]` 部分中定义。

**Microagent 配置**
- `micro_agent_name`
  - 类型: `str`
  - 默认值: `""`
  - 描述: 用于此 agent 的 micro agent 名称

**内存配置**
- `memory_enabled`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 是否启用长期记忆(embeddings)

- `memory_max_threads`
  - 类型: `int`
  - 默认值: `3`
  - 描述: 同时为 embeddings 编制索引的最大线程数

**LLM 配置**
- `llm_config`
  - 类型: `str`
  - 默认值: `'your-llm-config-group'`
  - 描述: 要使用的 LLM 配置的名称

**ActionSpace 配置**
- `function_calling`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 是否启用函数调用

- `codeact_enable_browsing`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 是否在 action space 中启用浏览代理(仅适用于函数调用)

- `codeact_enable_llm_editor`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 是否在 action space 中启用 LLM 编辑器(仅适用于函数调用)

- `codeact_enable_jupyter`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 是否在 action space 中启用 Jupyter

**Microagent 使用**
- `use_microagents`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 是否使用 microagents

- `disabled_microagents`
  - 类型: `list of str`
  - 默认值: `None`
  - 描述: 要禁用
