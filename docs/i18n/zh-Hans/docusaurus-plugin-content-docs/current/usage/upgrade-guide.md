以下是翻译后的内容:

# ⬆️ 升级指南

## 0.8.0 (2024-07-13)

### 配置中的重大变更

在此版本中,我们对后端配置引入了一些重大变更。如果你只通过前端(Web GUI)使用OpenHands,则无需处理任何事情。

以下是配置中重大变更的列表。它们仅适用于通过 `main.py` 使用 OpenHands CLI 的用户。更多详情,请参阅 [#2756](https://github.com/All-Hands-AI/OpenHands/pull/2756)。

#### 从 main.py 中移除 --model-name 选项

请注意,`--model-name` 或 `-m` 选项已不再存在。你应该在 `config.toml` 中设置 LLM 配置,或通过环境变量进行设置。

#### LLM 配置组必须是 'llm' 的子组

在 0.8 版本之前,你可以在 `config.toml` 中为 LLM 配置使用任意名称,例如:

```toml
[gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

然后使用 `--llm-config` CLI 参数按名称指定所需的 LLM 配置组。这已不再有效。相反,配置组必须位于 `llm` 组下,例如:

```toml
[llm.gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

如果你有一个名为 `llm` 的配置组,则无需更改它,它将被用作默认的 LLM 配置组。

#### 'agent' 组不再包含 'name' 字段

在 0.8 版本之前,你可能有或没有一个名为 `agent` 的配置组,如下所示:

```toml
[agent]
name="CodeActAgent"
memory_max_threads=2
```

请注意,`name` 字段现已被移除。相反,你应该在 `core` 组下放置 `default_agent` 字段,例如:

```toml
[core]
# 其他配置
default_agent='CodeActAgent'

[agent]
llm_config='llm'
memory_max_threads=2

[agent.CodeActAgent]
llm_config='gpt-4o'
```

请注意,与 `llm` 子组类似,你也可以定义 `agent` 子组。此外,代理可以与特定的 LLM 配置组相关联。更多详情,请参阅 `config.template.toml` 中的示例。
