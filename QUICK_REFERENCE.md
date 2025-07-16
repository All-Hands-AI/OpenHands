# OpenHands + Ollama Quick Reference

## 🚀 Quick Start Commands

```bash
# 1. Start OpenHands with Ollama
./start-ollama.sh

# 2. Check if everything is working
./check-ollama-setup.sh

# 3. Access OpenHands
# Open http://localhost:3000 in your browser
```

## 📋 Essential Commands

| Command | Description |
|---------|-------------|
| `./start-ollama.sh` | Start OpenHands with Ollama |
| `./start-ollama.sh stop` | Stop OpenHands |
| `./start-ollama.sh restart` | Restart OpenHands |
| `./start-ollama.sh logs` | View logs |
| `./start-ollama.sh rebuild` | Rebuild and restart |
| `./check-ollama-setup.sh` | Health check |

## 🔧 Ollama Commands

```bash
# Start Ollama
ollama serve

# Pull DeepSeek models
ollama pull deepseek-coder-v2:latest
ollama pull deepseek-r1:14b

# List available models
ollama list

# Test model
ollama run deepseek-coder-v2:latest "Hello!"
```

## 🌐 URLs

- **OpenHands Web UI**: http://localhost:3000
- **Ollama API**: http://localhost:11434
- **Ollama Models**: http://localhost:11434/api/tags

## 📁 Key Files

- `config.toml` - Main configuration
- `docker-compose.ollama.yml` - Docker setup
- `start-ollama.sh` - Startup script
- `check-ollama-setup.sh` - Health check
- `OLLAMA_SETUP.md` - Detailed guide

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't connect to Ollama | Run `ollama serve` |
| Models not found | Run `ollama pull deepseek-coder-v2:latest` |
| Docker not running | Start Docker Desktop |
| Port 3000 in use | Stop other services or change port |

## ⚙️ Configuration

### Primary Model
- **Model**: `ollama/deepseek-coder-v2:latest`
- **URL**: `http://host.docker.internal:11434`
- **Use**: General coding tasks

### Alternative Model
- **Model**: `ollama/deepseek-r1:14b`
- **URL**: `http://host.docker.internal:11434`
- **Use**: Reasoning tasks

## 📊 Status Check

```bash
# Quick status check
docker ps | grep openhands
curl -s http://localhost:11434/api/tags | grep deepseek
curl -s http://localhost:3000 > /dev/null && echo "OpenHands OK"
```

## 🛠️ Development

```bash
# View container logs
docker logs openhands-ollama

# Access container shell
docker exec -it openhands-ollama bash

# Restart just the container
docker restart openhands-ollama
```

---
**Need help?** Check `OLLAMA_SETUP.md` for detailed instructions!
