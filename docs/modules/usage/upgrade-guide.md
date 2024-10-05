# ⬆️ Upgrade Guide

## 0.8.0 (2024-07-13)

### Config breaking changes

In this release we introduced a few breaking changes to backend configurations.
If you have only been using OpenHands via frontend (web GUI), nothing needs
to be taken care of.

Here's a list of breaking changes in configs. They only apply to users who
use OpenHands CLI via `main.py`. For more detail, see [#2756](https://github.com/All-Hands-AI/OpenHands/pull/2756).

#### Removal of --model-name option from main.py

Please note that `--model-name`, or `-m` option, no longer exists. You should set up the LLM
configs in `config.toml` or via environmental variables.

#### LLM config groups must be subgroups of 'llm'

Prior to release 0.8, you can use arbitrary name for llm config in `config.toml`, e.g.

```toml
[gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

and then use `--llm-config` CLI argument to specify the desired LLM config group
by name. This no longer works. Instead, the config group must be under `llm` group,
e.g.:

```toml
[llm.gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

If you have a config group named `llm`, no need to change it, it will be used
as the default LLM config group.

#### 'agent' group no longer contains 'name' field

Prior to release 0.8, you may or may not have a config group named `agent` that
looks like this:

```toml
[agent]
name="CodeActAgent"
memory_max_threads=2
```

Note the `name` field is now removed. Instead, you should put `default_agent` field
under `core` group, e.g.

```toml
[core]
# other configs
default_agent='CodeActAgent'

[agent]
llm_config='llm'
memory_max_threads=2

[agent.CodeActAgent]
llm_config='gpt-4o'
```

Note that similar to `llm` subgroups, you can also define `agent` subgroups.
Moreover, an agent can be associated with a specific LLM config group. For more
detail, see the examples in `config.template.toml`.
