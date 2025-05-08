# 配置选项

:::note
本页概述了 OpenHands 的所有可用配置选项，允许您自定义其行为并将其与其他服务集成。在 GUI 模式下，通过设置界面应用的任何设置将优先生效。
:::

## 核心配置

核心配置选项在 `config.toml` 文件的 `[core]` 部分中定义。

### API 密钥
- `e2b_api_key`
  - 类型: `str`
  - 默认值: `""`
  - 描述: E2B 的 API 密钥

- `modal_api_token_id`
  - 类型: `str`
  - 默认值: `""`
  - 描述: Modal 的 API 令牌 ID

- `modal_api_token_secret`
  - 类型: `str`
  - 默认值: `""`
  - 描述: Modal 的 API 令牌密钥

### 工作区
- `workspace_base` **(已弃用)**
  - 类型: `str`
  - 默认值: `"./workspace"`
  - 描述: 工作区的基本路径。**已弃用：请使用 `SANDBOX_VOLUMES` 代替。**

- `cache_dir`
  - 类型: `str`
  - 默认值: `"/tmp/cache"`
  - 描述: 缓存目录路径

### 调试和日志
- `debug`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 启用调试

- `disable_color`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 在终端输出中禁用颜色

### 轨迹
- `save_trajectory_path`
  - 类型: `str`
  - 默认值: `"./trajectories"`
  - 描述: 存储轨迹的路径（可以是文件夹或文件）。如果是文件夹，轨迹将保存在该文件夹中以会话 ID 命名并带有 .json 扩展名的文件中。

- `replay_trajectory_path`
  - 类型: `str`
  - 默认值: `""`
  - 描述: 加载并重放轨迹的路径。如果提供，必须是 JSON 格式的轨迹文件路径。轨迹文件中的操作将在执行任何用户指令之前先重放。

### 文件存储
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
  - 描述: 上传文件的最大大小，以兆字节为单位

- `file_uploads_restrict_file_types`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 限制文件上传的文件类型

- `file_uploads_allowed_extensions`
  - 类型: `list of str`
  - 默认值: `[".*"]`
  - 描述: 允许上传的文件扩展名列表

### 任务管理
- `max_budget_per_task`
  - 类型: `float`
  - 默认值: `0.0`
  - 描述: 每个任务的最大预算（0.0 表示无限制）

- `max_iterations`
  - 类型: `int`
  - 默认值: `100`
  - 描述: 最大迭代次数

### 沙盒配置
- `volumes`
  - 类型: `str`
  - 默认值: `None`
  - 描述: 格式为 'host_path:container_path[:mode]' 的卷挂载，例如 '/my/host/dir:/workspace:rw'。可以使用逗号指定多个挂载，例如 '/path1:/workspace/path1,/path2:/workspace/path2:ro'

- `workspace_mount_path_in_sandbox` **(已弃用)**
  - 类型: `str`
  - 默认值: `"/workspace"`
  - 描述: 在沙盒中挂载工作区的路径。**已弃用：请使用 `SANDBOX_VOLUMES` 代替。**

- `workspace_mount_path` **(已弃用)**
  - 类型: `str`
  - 默认值: `""`
  - 描述: 挂载工作区的路径。**已弃用：请使用 `SANDBOX_VOLUMES` 代替。**

- `workspace_mount_rewrite` **(已弃用)**
  - 类型: `str`
  - 默认值: `""`
  - 描述: 将工作区挂载路径重写为的路径。通常可以忽略此项，它指的是在另一个容器内运行的特殊情况。**已弃用：请使用 `SANDBOX_VOLUMES` 代替。**

### 其他
- `run_as_openhands`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 作为 OpenHands 运行

- `runtime`
  - 类型: `str`
  - 默认值: `"docker"`
  - 描述: 运行时环境

- `default_agent`
  - 类型: `str`
  - 默认值: `"CodeActAgent"`
  - 描述: 默认代理的名称

- `jwt_secret`
  - 类型: `str`
  - 默认值: `uuid.uuid4().hex`
  - 描述: 用于身份验证的 JWT 密钥。请设置为您自己的值。

## LLM 配置

LLM（大型语言模型）配置选项在 `config.toml` 文件的 `[llm]` 部分中定义。

要在 docker 命令中使用这些选项，请传入 `-e LLM_<option>`。例如：`-e LLM_NUM_RETRIES`。

:::note
对于开发设置，您还可以定义自定义命名的 LLM 配置。有关详细信息，请参阅[自定义 LLM 配置](./llms/custom-llm-configs)。
:::

**AWS 凭证**
- `aws_access_key_id`
  - 类型: `str`
  - 默认值: `""`
  - 描述: AWS 访问密钥 ID

- `aws_region_name`
  - 类型: `str`
  - 默认值: `""`
  - 描述: AWS 区域名称

- `aws_secret_access_key`
  - 类型: `str`
  - 默认值: `""`
  - 描述: AWS 秘密访问密钥

### API 配置
- `api_key`
  - 类型: `str`
  - 默认值: `None`
  - 描述: 要使用的 API 密钥

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
  - 描述: 每个输入令牌的成本

- `output_cost_per_token`
  - 类型: `float`
  - 默认值: `0.0`
  - 描述: 每个输出令牌的成本

### 自定义 LLM 提供商
- `custom_llm_provider`
  - 类型: `str`
  - 默认值: `""`
  - 描述: 自定义 LLM 提供商

### 消息处理
- `max_message_chars`
  - 类型: `int`
  - 默认值: `30000`
  - 描述: 包含在提示中发送给 LLM 的事件内容的大致最大字符数。较大的观察结果会被截断。

- `max_input_tokens`
  - 类型: `int`
  - 默认值: `0`
  - 描述: 最大输入令牌数

- `max_output_tokens`
  - 类型: `int`
  - 默认值: `0`
  - 描述: 最大输出令牌数

### 模型选择
- `model`
  - 类型: `str`
  - 默认值: `"claude-3-5-sonnet-20241022"`
  - 描述: 要使用的模型

### 重试
- `num_retries`
  - 类型: `int`
  - 默认值: `8`
  - 描述: 尝试重试的次数

- `retry_max_wait`
  - 类型: `int`
  - 默认值: `120`
  - 描述: 重试尝试之间的最大等待时间（以秒为单位）

- `retry_min_wait`
  - 类型: `int`
  - 默认值: `15`
  - 描述: 重试尝试之间的最小等待时间（以秒为单位）

- `retry_multiplier`
  - 类型: `float`
  - 默认值: `2.0`
  - 描述: 指数退避计算的乘数

### 高级选项
- `drop_params`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 删除任何未映射（不支持）的参数而不引发异常

- `caching_prompt`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 如果 LLM 提供并支持，则使用提示缓存功能

- `ollama_base_url`
  - 类型: `str`
  - 默认值: `""`
  - 描述: OLLAMA API 的基础 URL

- `temperature`
  - 类型: `float`
  - 默认值: `0.0`
  - 描述: API 的温度参数

- `timeout`
  - 类型: `int`
  - 默认值: `0`
  - 描述: API 的超时时间

- `top_p`
  - 类型: `float`
  - 默认值: `1.0`
  - 描述: API 的 top p 参数

- `disable_vision`
  - 类型: `bool`
  - 默认值: `None`
  - 描述: 如果模型具有视觉能力，此选项允许禁用图像处理（对于成本降低很有用）

## 代理配置

代理配置选项在 `config.toml` 文件的 `[agent]` 和 `[agent.<agent_name>]` 部分中定义。

### LLM 配置
- `llm_config`
  - 类型: `str`
  - 默认值: `'your-llm-config-group'`
  - 描述: 要使用的 LLM 配置的名称

### ActionSpace 配置
- `function_calling`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 是否启用函数调用

- `enable_browsing`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 是否在操作空间中启用浏览代理（仅适用于函数调用）

- `enable_llm_editor`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 是否在操作空间中启用 LLM 编辑器（仅适用于函数调用）

- `enable_jupyter`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 是否在操作空间中启用 Jupyter

- `enable_history_truncation`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 当达到 LLM 上下文长度限制时，是否应截断历史记录以继续会话

### 微代理使用
- `enable_prompt_extensions`
  - 类型: `bool`
  - 默认值: `true`
  - 描述: 是否使用微代理

- `disabled_microagents`
  - 类型: `list of str`
  - 默认值: `None`
  - 描述: 要禁用的微代理列表

## 沙盒配置

沙盒配置选项在 `config.toml` 文件的 `[sandbox]` 部分中定义。

要在 docker 命令中使用这些选项，请传入 `-e SANDBOX_<option>`。例如：`-e SANDBOX_TIMEOUT`。

### 执行
- `timeout`
  - 类型: `int`
  - 默认值: `120`
  - 描述: 沙盒超时时间（以秒为单位）

- `user_id`
  - 类型: `int`
  - 默认值: `1000`
  - 描述: 沙盒用户 ID

### 容器镜像
- `base_container_image`
  - 类型: `str`
  - 默认值: `"nikolaik/python-nodejs:python3.12-nodejs22"`
  - 描述: 用于沙盒的容器镜像

### 网络
- `use_host_network`
  - 类型: `bool`
  - 默认值: `false`
  - 描述: 使用主机网络

- `runtime_binding_address`
  - 类型: `str`
  - 默认值: `0.0.0.0`
  - 描述: 运行时端口的绑定地址。它指定 Docker 应该将
