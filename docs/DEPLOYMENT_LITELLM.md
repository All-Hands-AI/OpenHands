# LiteLLM Load Balancing for Multiple Provider Keys

This document explains how to wire the app to a local LiteLLM proxy and configure multiple API keys per provider to improve throughput and reduce rate-limit errors.

## Overview
- Run LiteLLM as a sidecar service via Docker Compose
- Provide multiple keys for each provider (comma-separated)
- Point the app at LiteLLM using a single master key
- Choose a default model (e.g., `openai/gpt-4o`, `gemini/gemini-1.5-pro`, `mistral/mistral-large-latest`, or an OpenRouter model)

## 1) Create a local override
Create `docker-compose.override.yml` (it is already git-ignored) in the project root:

```yaml
services:
  openhands:
    env_file:
      - .env.app

  litellm:
    image: ghcr.io/berriai/litellm:main
    environment:
      # Comma-separated keys for each provider
      OPENAI_API_KEYS: sk-openai-1,sk-openai-2
      GEMINI_API_KEYS: AIza-gemini-1,AIza-gemini-2
      MISTRAL_API_KEYS: sk-mistral-1,sk-mistral-2
      OPENROUTER_API_KEYS: sk-or-1,sk-or-2
      # Master key to protect the proxy
      LITELLM_MASTER_KEY: super-secret-master-key
    command: --port 4000 --num_workers 2 --telemetry False
    restart: unless-stopped
```

## 2) App environment
Create `.env.app` (also git-ignored) to point the app to LiteLLM:

```bash
# LLM routing via LiteLLM
LLM_BASE_URL=http://litellm:4000
LLM_API_KEY=super-secret-master-key
LLM_MODEL=openai/gpt-4o

# Hide LLM settings in the UI for end users (optional)
HIDE_LLM_SETTINGS=true

# Enable cookie-based GitHub SSO auth
OPENHANDS_CONFIG_CLS=openhands.server.config.server_config.CursorLikeServerConfig

# GitHub OAuth (server-side)
GITHUB_APP_CLIENT_ID=...
GITHUB_APP_CLIENT_SECRET=...
FRONTEND_REDIRECT_URL=https://your-domain
```

## 3) Start
```bash
docker compose up -d --build
```

## Notes
- Do NOT commit real keys. Keep them in `.env.app`/override only
- You can change default model by updating `LLM_MODEL`
- LiteLLM will round-robin and retry across keys to mitigate rate limits
- You can add more providers by setting additional env vars supported by LiteLLM