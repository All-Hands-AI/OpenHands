# Model Routing Module

**⚠️ Experimental Feature**: This module is experimental and under active development.

## Overview

Model routing enables OpenHands to switch between different LLM models during a conversation. An example use case is routing between a primary (expensive, multimodal) model and a secondary (cheaper, text-only) model.

## Available Routers

- **`noop_router`** (default): No routing, always uses main LLM
- **`rule_based_cv_router`**: Cost-saving router that switches based on:
  - Routes to primary model for images or when secondary model's context limit is exceeded
  - Uses secondary model for text-only requests within limits

## Configuration

Add to your `config.toml`:

```toml
# Main LLM (primary model)
[llm]
model = "gpt-4o"
api_key = "your-api-key"

# Secondary model for routing
[llm.secondary_model]
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
