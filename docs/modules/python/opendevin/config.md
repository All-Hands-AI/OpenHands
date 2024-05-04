---
sidebar_label: config
title: opendevin.config
---

## LLMConfig Objects

```python
@dataclass
class LLMConfig(metaclass=Singleton)
```

#### defaults\_to\_dict

```python
def defaults_to_dict() -> dict
```

Serialize fields to a dict for the frontend, including type hints, defaults, and whether it&#x27;s optional.

## AgentConfig Objects

```python
@dataclass
class AgentConfig(metaclass=Singleton)
```

#### defaults\_to\_dict

```python
def defaults_to_dict() -> dict
```

Serialize fields to a dict for the frontend, including type hints, defaults, and whether it&#x27;s optional.

## AppConfig Objects

```python
@dataclass
class AppConfig(metaclass=Singleton)
```

#### \_\_post\_init\_\_

```python
def __post_init__()
```

Post-initialization hook, called when the instance is created with only default values.

#### defaults\_to\_dict

```python
def defaults_to_dict() -> dict
```

Serialize fields to a dict for the frontend, including type hints, defaults, and whether it&#x27;s optional.

#### get\_field\_info

```python
def get_field_info(field)
```

Extract information about a dataclass field: type, optional, and default value.

#### load\_from\_env

```python
def load_from_env(config: AppConfig, env_or_toml_dict: dict | os._Environ)
```

Reads the env-style vars and sets config attributes based on env vars or a config.toml dict.
Compatibility with vars like LLM_BASE_URL, AGENT_MEMORY_ENABLED and others.

**Arguments**:

- `config` - The AppConfig object to set attributes on.
- `env_or_toml_dict` - The environment variables or a config.toml dict.

#### load\_from\_toml

```python
def load_from_toml(config: AppConfig)
```

Load the config from the toml file. Supports both styles of config vars.

**Arguments**:

- `config` - The AppConfig object to update attributes of.

#### finalize\_config

```python
def finalize_config(config: AppConfig)
```

More tweaks to the config after it&#x27;s been loaded.

#### get\_parser

```python
def get_parser()
```

Get the parser for the command line arguments.

#### parse\_arguments

```python
def parse_arguments()
```

Parse the command line arguments.

