# DeepSeek R1-0528 Integration Guide

This guide explains how to use DeepSeek R1-0528 as an alternative LLM option in OpenHands, including fallback functionality for cost-effective AI assistance.

## Overview

DeepSeek R1-0528 is a powerful and cost-effective language model that can serve as:
- A primary LLM for budget-conscious users
- A fallback option when premium APIs fail or are unavailable
- A reasoning-enhanced model for complex tasks

## Key Features

- **Cost-Effective**: ~$0.014 per 1K input tokens, $0.028 per 1K output tokens
- **Function Calling**: Full support for OpenHands tool usage
- **Reasoning Enhancement**: Automatic step-by-step reasoning for complex tasks
- **Automatic Fallback**: Seamless switching when primary models fail
- **Performance Optimized**: Specialized configurations for best results

## Quick Start

### 1. Basic DeepSeek R1-0528 Usage

```toml
# config.toml
[llm]
model = "deepseek-r1-0528"
api_key = "your-deepseek-api-key"
base_url = "https://api.deepseek.com"
temperature = 0.0
max_output_tokens = 4096
```

### 2. Using DeepSeek as Fallback

```toml
# config.toml
[llm]
model = "gpt-4o"
api_key = "your-openai-key"
enable_fallback = true
fallback_models = ["deepseek-r1-0528"]
auto_fallback_on_error = true

[llm.fallback_api_keys]
"deepseek-r1-0528" = "your-deepseek-api-key"

[llm.fallback_base_urls]
"deepseek-r1-0528" = "https://api.deepseek.com"
```

### 3. Environment Variables

```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export OPENAI_API_KEY="your-openai-key"  # For primary model
```

## Advanced Configuration

### Enhanced LLM with Automatic Fallback

```python
from openhands.core.config import LLMConfig
from openhands.llm import EnhancedLLM

# Create primary configuration
primary_config = LLMConfig(
    model="gpt-4o",
    api_key="your-openai-key"
)

# Create enhanced LLM with DeepSeek fallback
llm = EnhancedLLM(
    config=primary_config,
    enable_auto_fallback=True
)

# The LLM will automatically fallback to DeepSeek if OpenAI fails
response = llm.completion(messages=[
    {"role": "user", "content": "Analyze this code and suggest improvements"}
])
```

### Direct DeepSeek R1 Usage

```python
from openhands.llm.deepseek_r1 import create_deepseek_r1_llm

# Create optimized DeepSeek R1 instance
llm = create_deepseek_r1_llm(
    api_key="your-deepseek-api-key",
    temperature=0.0,
    max_output_tokens=4096
)

# Use for complex reasoning tasks
response = llm.completion(messages=[
    {"role": "user", "content": "Debug this complex algorithm step by step"}
])
```

### Fallback Manager

```python
from openhands.llm.fallback_manager import FallbackManager, create_deepseek_fallback_config
from openhands.core.config import LLMConfig

# Create configurations
primary_config = LLMConfig(model="gpt-4o", api_key="openai-key")
deepseek_config = create_deepseek_fallback_config("deepseek-key")

# Create fallback manager
manager = FallbackManager(primary_config, [deepseek_config])

# Use with automatic fallback
response = manager.completion(messages=[
    {"role": "user", "content": "Help me solve this problem"}
])

# Check provider health
status = manager.get_provider_status()
print(f"Provider status: {status}")
```

## Configuration Options

### DeepSeek R1 Specific Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `model` | `deepseek-r1-0528` | Model identifier |
| `base_url` | `https://api.deepseek.com` | API endpoint |
| `temperature` | `0.0` | Sampling temperature |
| `max_output_tokens` | `4096` | Maximum response length |
| `top_p` | `0.95` | Nucleus sampling parameter |
| `timeout` | `60` | Request timeout in seconds |

### Fallback Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_fallback` | `false` | Enable automatic fallback |
| `fallback_models` | `[]` | List of fallback models |
| `fallback_api_keys` | `{}` | API keys for fallback models |
| `fallback_base_urls` | `{}` | Base URLs for fallback models |
| `auto_fallback_on_error` | `true` | Auto-switch on errors |
| `fallback_max_retries` | `2` | Max retries per fallback model |

## Performance Optimizations

### Reasoning Enhancement

DeepSeek R1 automatically enhances complex tasks with reasoning prompts:

```python
# This task will automatically get reasoning enhancement
response = llm.completion(messages=[
    {"role": "user", "content": "Analyze and debug this complex code"}
])

# The model receives an enhanced prompt like:
# "Please think through this step by step and show your reasoning process.
#  Consider multiple approaches and explain your thought process.
#
#  Analyze and debug this complex code"
```

### Cost Estimation

```python
from openhands.llm.deepseek_r1 import estimate_deepseek_r1_cost

# Estimate cost for a request
cost = estimate_deepseek_r1_cost(
    input_tokens=1000,
    output_tokens=500,
    model="deepseek-r1-0528"
)
print(f"Estimated cost: ${cost:.6f}")
```

## Best Practices

### 1. Use DeepSeek for Cost-Sensitive Applications

```toml
# For development and testing
[llm.development]
model = "deepseek-r1-0528"
api_key = "your-deepseek-key"

# For production with fallback
[llm.production]
model = "gpt-4o"
api_key = "your-openai-key"
enable_fallback = true
fallback_models = ["deepseek-r1-0528"]
```

### 2. Configure Appropriate Timeouts

```toml
[llm]
model = "deepseek-r1-0528"
timeout = 60  # DeepSeek R1 may take longer for complex reasoning
num_retries = 3
retry_min_wait = 2
retry_max_wait = 10
```

### 3. Monitor Provider Health

```python
# Check fallback status periodically
status = enhanced_llm.get_fallback_status()
for provider, health in status.items():
    if not health['is_healthy']:
        print(f"Provider {provider} is unhealthy: {health['failure_count']} failures")

# Reset health if needed
enhanced_llm.reset_fallback_health()
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```bash
   export DEEPSEEK_API_KEY="your-actual-api-key"
   ```

2. **Connection Timeout**
   ```toml
   [llm]
   timeout = 120  # Increase timeout for complex tasks
   ```

3. **Fallback Not Working**
   ```toml
   [llm]
   enable_fallback = true
   auto_fallback_on_error = true
   ```

### Debug Mode

```python
import logging
logging.getLogger('openhands.llm').setLevel(logging.DEBUG)

# This will show detailed fallback behavior
```

## Migration Guide

### From Standard LLM to Enhanced LLM

```python
# Before
from openhands.llm import LLM
llm = LLM(config)

# After
from openhands.llm import EnhancedLLM
llm = EnhancedLLM(config, enable_auto_fallback=True)
```

### Adding DeepSeek to Existing Configuration

```toml
# Add to existing config.toml
[llm]
# ... existing settings ...
enable_fallback = true
fallback_models = ["deepseek-r1-0528"]

[llm.fallback_api_keys]
"deepseek-r1-0528" = "your-deepseek-key"
```

## API Reference

See the following modules for detailed API documentation:

- `openhands.llm.enhanced_llm.EnhancedLLM` - Main enhanced LLM class
- `openhands.llm.fallback_manager.FallbackManager` - Fallback orchestration
- `openhands.llm.deepseek_r1` - DeepSeek R1 specific optimizations
- `openhands.core.config.LLMConfig` - Configuration options

## Support

For issues related to DeepSeek R1 integration:

1. Check the [OpenHands documentation](https://docs.all-hands.dev/)
2. Review the configuration examples above
3. Enable debug logging for detailed error information
4. Open an issue on the [OpenHands GitHub repository](https://github.com/All-Hands-AI/OpenHands)
