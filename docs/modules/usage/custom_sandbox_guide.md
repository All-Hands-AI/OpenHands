# 💿 Creating a Custom Docker Sandbox

The default OpenDevin sandbox uses a [minimal Ubuntu configuration](https://github.com/OpenDevin/OpenDevin/blob/main/containers/sandbox/Dockerfile). This guide will help you create a custom Docker sandbox with additional software pre-installed.

## Setup

1. Clone the OpenDevin GitHub repository.
2. In the root (OpenDevin/) directory, run:
   ```
   make build
   make run
   ```
3. Navigate to `localhost:3001` to verify your local OpenDevin build.

For detailed installation instructions, refer to [Development.md](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md).

## Create Your Docker Image

1. Create a Dockerfile (e.g., to include Node.js):
   ```dockerfile
   FROM ubuntu:latest
   RUN apt-get update && apt-get install -y nodejs
   ```
2. Build your image:
   ```
   docker build -t custom_image .
   ```

Note: Install packages for all users, as OpenDevin runs as user "opendevin" in the sandbox.

## Specify Custom Image in config.toml

Create a `config.toml` file in the OpenDevin directory:

```toml
[core]
workspace_base="./workspace"
persist_sandbox=false
run_as_devin=true
sandbox_container_image="custom_image"
```

## Run and Verify

1. Run `make run` in the top-level directory.
2. Navigate to `localhost:3001` and check for your desired dependencies (e.g., `node -v`).

## Technical Explanation

The process is handled by [ssh_box.py](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/ssh_box.py) and [image_agnostic_util.py](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py).

## Troubleshooting

- **UID 1000 not unique:** Modify `sandbox_user_id` in `config.toml`:
  ```toml
  sandbox_user_id="1001"
  ```
- **Port use errors:** Delete all running Docker containers and re-run `make run`.

For additional help, join our [Slack](https://join.slack.com/t/opendevin/shared_invite/zt-2jsrl32uf-fTeeFjNyNYxqSZt5NPY3fA) or [Discord](https://discord.gg/ESHStjSjD4) communities.