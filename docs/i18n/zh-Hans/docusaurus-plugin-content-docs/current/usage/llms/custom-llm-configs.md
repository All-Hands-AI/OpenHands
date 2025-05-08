# 自定义 LLM 配置

OpenHands 支持在 `config.toml` 文件中定义多个命名的 LLM 配置。此功能允许您针对不同目的使用不同的 LLM 配置，例如对不需要高质量响应的任务使用更经济的模型，或者为特定代理使用具有不同参数的不同模型。

## 工作原理

命名的 LLM 配置在 `config.toml` 文件中使用以 `llm.` 开头的部分定义。例如：

```toml
# 默认 LLM 配置
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# 更经济模型的自定义 LLM 配置
[llm.gpt3]
model = "gpt-3.5-turbo"
api_key = "your-api-key"
temperature = 0.2

# 另一个具有不同参数的自定义配置
[llm.high-creativity]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.8
top_p = 0.9
```

每个命名配置都从默认的 `[llm]` 部分继承所有设置，并可以覆盖任何这些设置。您可以根据需要定义任意数量的自定义配置。

## 使用自定义配置

### 与代理一起使用

您可以通过在代理的配置部分设置 `llm_config` 参数来指定代理应使用哪个 LLM 配置：

```toml
[agent.RepoExplorerAgent]
# 为此代理使用更经济的 GPT-3 配置
llm_config = 'gpt3'

[agent.CodeWriterAgent]
# 为此代理使用高创造力配置
llm_config = 'high-creativity'
```

### 配置选项

每个命名的 LLM 配置支持与默认 LLM 配置相同的所有选项。这些包括：

- 模型选择 (`model`)
- API 配置 (`api_key`, `base_url` 等)
- 模型参数 (`temperature`, `top_p` 等)
- 重试设置 (`num_retries`, `retry_multiplier` 等)
- 令牌限制 (`max_input_tokens`, `max_output_tokens`)
- 以及所有其他 LLM 配置选项

有关可用选项的完整列表，请参阅 [配置选项](../configuration-options) 文档中的 LLM 配置部分。

## 使用场景

自定义 LLM 配置在几种情况下特别有用：

- **成本优化**：对不需要高质量响应的任务使用更经济的模型，如代码库探索或简单的文件操作。
- **任务特定调整**：为需要不同创造力或确定性水平的任务配置不同的 temperature 和 top_p 值。
- **不同提供商**：为不同任务使用不同的 LLM 提供商或 API 端点。
- **测试和开发**：在开发和测试期间轻松切换不同的模型配置。

## 示例：成本优化

使用自定义 LLM 配置优化成本的实用示例：

```toml
# 使用 GPT-4 的默认配置，用于高质量响应
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# 用于代码库探索的更经济配置
[llm.repo-explorer]
model = "gpt-3.5-turbo"
temperature = 0.2

# 用于代码生成的配置
[llm.code-gen]
model = "gpt-4"
temperature = 0.0
max_output_tokens = 2000

[agent.RepoExplorerAgent]
llm_config = 'repo-explorer'

[agent.CodeWriterAgent]
llm_config = 'code-gen'
```

在此示例中：
- 代码库探索使用更经济的模型，因为它主要涉及理解和导航代码
- 代码生成使用 GPT-4，并具有更高的令牌限制，用于生成更大的代码块
- 默认配置仍可用于其他任务

# 具有保留名称的自定义配置

OpenHands 可以使用具有保留名称的自定义 LLM 配置，用于特定用例。如果您在保留名称下指定模型和其他设置，那么 OpenHands 将加载并将它们用于特定目的。目前，已实现了一种这样的配置：草稿编辑器。

## 草稿编辑器配置

`draft_editor` 配置是一组设置，您可以提供它来指定用于初步起草代码编辑的模型，适用于任何涉及编辑和优化代码的任务。您需要在 `[llm.draft_editor]` 部分下提供它。

例如，您可以在 `config.toml` 中定义一个草稿编辑器，如下所示：

```toml
[llm.draft_editor]
model = "gpt-4"
temperature = 0.2
top_p = 0.95
presence_penalty = 0.0
frequency_penalty = 0.0
```

此配置：
- 使用 GPT-4 进行高质量的编辑和建议
- 设置较低的温度 (0.2) 以保持一致性，同时允许一些灵活性
- 使用较高的 top_p 值 (0.95) 以考虑广泛的令牌选项
- 禁用存在和频率惩罚，以保持对所需特定编辑的关注

当您希望让 LLM 在进行编辑之前起草编辑时，请使用此配置。通常，它可能有助于：
- 审查并建议代码改进
- 优化现有内容，同时保持其核心含义
- 对代码或文本进行精确、有针对性的更改

:::note
自定义 LLM 配置仅在通过 `main.py` 或 `cli.py` 在开发模式下使用 OpenHands 时可用。当通过 `docker run` 运行时，请使用标准配置选项。
:::
