# Docker Support

- Pretending to be developer-friendly🤞
- With convenience for end-users 🕴️
- Runs from sources 🧾, no build is necessary
- Source directories are mapped into container directory to just run

# Opendevin Backend

- Docker image with GPU support with NVidia CUDA 12.4.0
- Python 3.11.8
- Miniconda3 environment:
Python packages are under conda control. No PIP🪦.
- Build caches shared between services for build performance
- Localization at OS level with 152 UTF-8 locales. Major and hieroglyphic languages with dialects are enabled by default.
  1. Uncomment necessary locales in `docker/locales` file
  2. Run `docker compose up --build --remove-orphans`

## UI

- Independent `docker compose` service
- Yarn package manager (available out-of-the-box, so no new dependencies) for seamless [NX integration](https://nx.dev/nx-api/react) with `@nx/react`. After many attempts it showed itself as the most robust for building this UI project.

## Dockerized OpenDevin

Use following sequence to have it up and running.

```shell
$ git clone https://github.com/OpenDevin/OpenDevin.git .
$ cd OpenDevin
$ docker compose up --build
```

Also `docker compose up --build app` will start application container with dependencies, as well as `docker compose up --build ui` will start the UI server.

### Components

 - OpenDevin service
 - LiteLLM Proxy service
 - Mitmproxy for debugging
 - Ollama LLM service
 - Postgres server
 - Redis server

### configuration using `.env` files
- Ports 
- Time zone configuration
- Directory paths

## Use as a systemd service

1. Clone the repository

`git clone https://github.com/lehcode/oppendevin.git /home/<your_username>/opendevin`

1. Stop or disable existing ollama

Temporarily stop or disable Ollama systemd service on host system to avoid running multiple Ollama services.

```shell
$ systemctl stop ollama.service
$ systemctl disable ollama.service
```

2. Create a systemd Service Unit File

Create a systemd service unit file (e.g., oppendevin.service) in the /etc/systemd/system/ directory:

```shell
sudo systemctl edit --full docker-compose@.opendevin.service
```

```ini
[Unit]
Description=Oppendevin systemd service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/<your_username>/opendevin
ExecStart=/usr/local/bin/docker-compose up up -d --remove-orphans
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

- Update the paths to docker-compose and docker-compose.yml as necessary.

3. Reload systemd and enable the service

After creating the systemd service unit file, reload systemd to load the new service and enable it to start automatically on boot.

```bash
sudo systemctl daemon-reload
sudo systemctl start oppendevin
```

Optionally enable service to start automatically on boot.

```bash
sudo systemctl enable oppendevin
```

## TODO

- **Describe all build features 🫤**
- Refactor UI build
- HMR and live reload for UI service in development mode
- Configure production build for user convenience
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher) integration
- [MemGPT](https://github.com/cpacker/MemGPT) integration
