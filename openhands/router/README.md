# Model Routing Module

**⚠️ Experimental Feature**: This module is experimental and under active development.

## Overview

Model routing enables OpenHands to switch between different LLM models during a conversation for cost optimization. The primary use case is routing between a strong (expensive, multimodal) model and a weak (cheaper, text-only) model.

## Available Routers

- **`noop_router`** (default): No routing, always uses main LLM
- **`rule_based_cv_router`**: Cost-saving router that switches based on:
  - Routes to strong model for images or when weak model's context limit is exceeded
  - Uses weak model for text-only requests within limits

## Configuration

Add to your `config.toml`:

```toml
# Main LLM (strong model)
[llm]
model = "gpt-4o"
api_key = "your-api-key"

# Weak model for routing
[llm.weak_model]
model = "gpt-4o-mini"
api_key = "your-api-key"
for_routing = true
max_input_tokens = 128000

# Enable routing
[model_routing]
router_name = "rule_based_cv_router"
```

## Extending

Create custom routers by inheriting from `BaseRouter` and implementing `set_active_llm()`. Register in `ROUTER_REGISTRY`.