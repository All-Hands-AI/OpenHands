---
sidebar_label: config
title: opendevin.config
---

## AppConfig Objects

```python
@dataclass
class AppConfig(metaclass=Singleton)
```

#### workspace\_mount\_path

TODO this might not work, set at the end

#### compat\_env\_to\_config

```python
def compat_env_to_config(config, env_or_toml_dict)
```

Reads the env-style vars and sets config attributes based on env vars or a config.toml dict.
Compatibility with vars like LLM_BASE_URL, AGENT_MEMORY_ENABLED and others.

**Arguments**:

- `config` - The AppConfig object to set attributes on.
- `env_or_toml_dict` - The environment variables or a config.toml dict.

