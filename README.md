<div align="center">
  <img src="https://i.ibb.co/7xN0Q0w6/RDn-Sl-NCCfl-I.jpg" 
       alt="GP-KhayaL Logo" 
       style="width:100%; max-height:400px; object-fit:contain; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.15);" />
  <h1>GP-KhayaL</h1>
  <p><em>Khayal Virtual Cyber Security</em></p>
</div>


## Overview
GP-KhayaL is a developer‑agent platform for working with code, repositories, and AI models. It provides a modern web UI, backend APIs, Git provider integrations, and an extensible runtime to open repositories, edit files, review diffs, commit, and create pull requests.

## Key Features
- GitHub/GitLab/Bitbucket integrations (personal token based)
- Open and browse repositories, edit files, and save changes
- Diff viewer and selective commit flow
- Branch creation and PR creation (GitHub supported)
- Chat panel streaming agent events and sending commands
- Job Center for long‑running tasks (e.g., clone) with status polling
- Flexible model selection via LiteLLM; custom display names for selected models

## Tech Stack
- Backend: Python 3.12, FastAPI, Uvicorn
- Frontend: React, Vite, TypeScript, Tailwind
- Integrations: LiteLLM for model routing, Git provider services
- Packaging: Poetry; Docker images for production

## Quick Start
### Run with Docker
```bash
docker compose up --build
```
Then open: `http://localhost:3000`

Optional environment hints (compose service `openhands`):
- `WORKSPACE_BASE=/absolute/path/to/workspace` to mount a local workspace
- `SANDBOX_USER_ID=0` (root) or a non‑root UID for the sandbox user

### Local Development
Requirements: Python 3.12, Poetry ≥ 1.8, Node.js ≥ 22
```bash
make build
make run
```
Open: `http://localhost:3000`

## Settings & Models
- Settings UI: choose provider/model, set API key(s), base URL, and other preferences
- Models are fetched dynamically via LiteLLM; examples include Anthropic Claude, OpenAI GPT, Google Gemini, and Mistral
- Custom display names (example mapping in UI):
  - `openai/gpt-4o` → `GP-K`
  - `anthropic/claude-3-5-sonnet-20241022` → `KhayaL-AI`
  - `google/gemini-1.5-pro` → `YE-21`
  - `openai/gpt-5-2025-08-07` → `Khayal-Pro`

## Repository Operations
- Open repo (background clone), browse tree, read/write file
- View diffs and commit selected files with a message
- Create a branch and push
- Create a PR (GitHub) and receive the PR URL

## Core Endpoints (selection)
- User/Git:
  - `GET /api/user/installations`
  - `GET /api/user/repositories`
  - `POST /api/add-git-providers`
- Sessions & Commands:
  - `POST /api/options/sessions` → returns `conversation_id`
  - `POST /api/options/commands` → send a command to the session
- Repo (per conversation):
  - `POST /api/conversations/{id}/repos/open` (background job)
  - `GET /api/conversations/{id}/repos/jobs/{job_id}`
  - `GET /api/conversations/{id}/repos/tree`
  - `GET /api/conversations/{id}/repos/file` / `PUT /api/conversations/{id}/repos/file`
  - `GET /api/conversations/{id}/repos/diff`
  - `POST /api/conversations/{id}/repos/branch`
  - `POST /api/conversations/{id}/repos/commit`
  - `POST /api/conversations/{id}/repos/pr`

## UI Highlights
- Sidebar branding with project name and tagline
- Pages: Connect GitHub, Workspace (Tree + Editor + Git Bar + Jobs), Chat, Settings
- Diff viewer (split/inline) and selective commit from Changes tab

## Production Image
A production image is built via `containers/app/Dockerfile` which bundles the frontend build into the backend image and launches FastAPI with Uvicorn.

### Build manually
```bash
docker build -t gp-khayal:latest -f containers/app/Dockerfile .
```

## Notes
- Configure your LLM provider and API key(s) in Settings before starting agent tasks
- For sharing a temporary public link during testing, you can use a tunneling tool (e.g., Cloudflare Tunnel) pointing to `http://localhost:3000`

---

This repository is branded as “GP‑KhayaL – Khayal Virtual Cyber Security”.
