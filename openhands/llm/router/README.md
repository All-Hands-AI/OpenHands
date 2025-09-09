# Model Routing Module

**⚠️ Experimental Feature**: This module is experimental and under active development.

## Overview

Model routing enables OpenHands to switch between different LLM models during a conversation. An example use case is routing between a primary (expensive, multimodal) model and a secondary (cheaper, text-only) model.

## Available Routers

- **`noop_router`** (default): No routing, always uses primary LLM
- **`multimodal_router`**: A router that switches based on:
  - Routes to primary model for images or when secondary model's context limit is exceeded
  - Uses secondary model for text-only requests within its context limit

## Configuration

Add to your `config.toml`:

```toml
# Main LLM (primary model)
[llm]
model = "claude-sonnet-4"
api_key = "your-api-key"

# Secondary model for routing
[llm.secondary_model]
model = "kimi-k2"
api_key = "your-api-key"
for_routing = true

# Enable routing
[model_routing]
router_name = "multimodal_router"
```

## Extending

Create custom routers by inheriting from `BaseRouter` and implementing `set_active_llm()`. Register in `ROUTER_REGISTRY`.
