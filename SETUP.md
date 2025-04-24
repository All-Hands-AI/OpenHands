# Init

- cp config.template.toml config.toml
- touch .env
- docker compose up
- curl -sSL https://install.python-poetry.org | python3.12
- make build
- make run

if you need debug log trace

- debug=1 make run

# Troubleshoot

- MCP not connect? Check VPN
