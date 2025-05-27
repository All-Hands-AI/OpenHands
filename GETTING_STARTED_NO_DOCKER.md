# Getting Started Without Docker

This guide will help you set up and run OpenHands on your local machine **without Docker**. It covers prerequisites, installation, configuration, and running the project. Optional dependencies (VS Code, Jupyter, browser) are clearly marked.

---

## 1. Prerequisites

- **Python 3.9+** (with `pip`)
- **tmux** (Linux/Mac) or **PowerShell** (Windows)
- **git**
- (Optional) [VS Code](https://code.visualstudio.com/), Jupyter, and a modern web browser

> **Security Warning:**
> The Local Runtime runs without sandbox isolation. The agent can directly access and modify files on your machine. Only use this runtime in controlled environments or when you fully understand the security implications.

---

## 2. Clone the Repository

```bash
git clone https://github.com/All-Hands-AI/OpenHands.git
cd OpenHands
```

---

## 3. Install Python Dependencies

We recommend using [Poetry](https://python-poetry.org/) for dependency management:

```bash
pip install poetry
poetry install
```

---

## 4. Configuration

You can configure OpenHands using environment variables or a `config.toml` file.

### Option A: Environment Variables

```bash
# Required
export RUNTIME=local

# Optional but recommended: mount your project directory
export SANDBOX_VOLUMES=/path/to/your/project:/workspace:rw
# For read-only data, use a different mount path
# export SANDBOX_VOLUMES=/path/to/your/project:/workspace:rw,/path/to/large/dataset:/data:ro
```

### Option B: config.toml

Copy the template and edit as needed:

```bash
cp config.template.toml config.toml
```

Edit `config.toml`:

```toml
[core]
runtime = "local"

[sandbox]
volumes = "/path/to/your/project:/workspace:rw"
# For read-only data, use a different mount path
# volumes = "/path/to/your/project:/workspace:rw,/path/to/large/dataset:/data:ro"
```

If `SANDBOX_VOLUMES` is not set, a temporary directory will be used.

---

## 5. Running OpenHands (Headless Mode)

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

---

## 6. Optional: VS Code, Jupyter, and Browser

- **VS Code**: For a rich editing experience, install [VS Code](https://code.visualstudio.com/) and the Python extension.
- **Jupyter**: For interactive notebooks, install Jupyter with `pip install notebook`.
- **Browser**: For web-based UIs, use any modern browser.

These are not required for headless or CLI usage.

---

## 7. Troubleshooting

- Ensure all prerequisites are installed and available in your `PATH`.
- If you encounter issues, check the [Development.md](./Development.md) for advanced setup and troubleshooting tips.
- For Windows users, only CLI and headless modes are supported with the Local Runtime.

---

## 8. More Information

- [Local Runtime Documentation](docs/modules/usage/runtimes/local.md)
- [Development Workflow](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)
- [OpenHands GitHub](https://github.com/All-Hands-AI/OpenHands)
