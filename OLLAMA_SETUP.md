# OpenHands with Local Ollama DeepSeek Models Setup Guide

This guide will help you set up OpenHands to work with your local Ollama instance running DeepSeek models (`deepseek-coder-v2:latest` and `deepseek-r1:14b`).

## Prerequisites

1. **Docker**: Ensure Docker is installed and running on your system
2. **Ollama**: Have Ollama installed and running with your DeepSeek models
3. **DeepSeek Models**: The following models should be available in your Ollama instance:
   - `deepseek-coder-v2:latest`
   - `deepseek-r1:14b`

## Quick Start

### 1. Prepare Your Ollama Models

First, ensure your Ollama service is running and has the required models:

```bash
# Start Ollama (if not already running)
ollama serve

# Pull the DeepSeek models (if not already available)
ollama pull deepseek-coder-v2:latest
ollama pull deepseek-r1:14b

# Verify models are available
ollama list
```

### 2. Run OpenHands with Ollama

Use the provided startup script for an automated setup:

```bash
# Make the script executable (if not already done)
chmod +x start-ollama.sh

# Start OpenHands with Ollama
./start-ollama.sh
```

The script will:
- Check if Docker is running
- Verify Ollama connectivity
- Check for available DeepSeek models
- Build the OpenHands Docker image
- Start the service

### 3. Access OpenHands

Once started, access OpenHands at: **http://localhost:3000**

## Manual Setup (Alternative)

If you prefer manual setup or need to customize the configuration:

### 1. Configuration File

The `config.toml` file is pre-configured for your setup. Key settings:

```toml
[llm]
model = "ollama/deepseek-coder-v2:latest"
ollama_base_url = "http://host.docker.internal:11434"
temperature = 0.1
max_output_tokens = 4096

[llm.deepseek-r1]
model = "ollama/deepseek-r1:14b"
ollama_base_url = "http://host.docker.internal:11434"
```

### 2. Docker Compose

Use the specialized Docker Compose file:

```bash
# Build and start
docker-compose -f docker-compose.ollama.yml up -d

# View logs
docker-compose -f docker-compose.ollama.yml logs -f

# Stop
docker-compose -f docker-compose.ollama.yml down
```

## Script Commands

The `start-ollama.sh` script supports several commands:

```bash
# Start OpenHands (default)
./start-ollama.sh

# Stop OpenHands
./start-ollama.sh stop

# View logs
./start-ollama.sh logs

# Restart OpenHands
./start-ollama.sh restart

# Rebuild and restart (useful after code changes)
./start-ollama.sh rebuild
```

## Configuration Details

### Model Selection

The configuration includes two model setups:

1. **Primary Model**: `ollama/deepseek-coder-v2:latest`
   - Optimized for coding tasks
   - Used as the default model

2. **Alternative Model**: `ollama/deepseek-r1:14b`
   - Available as `deepseek-r1` configuration
   - Can be selected in the UI or via configuration

### Network Configuration

- **Ollama URL**: `http://host.docker.internal:11434`
  - This allows the Docker container to access Ollama running on the host
  - If Ollama is on a different machine, update the URL in `config.toml`

### Performance Settings

- **Temperature**: Set to 0.1 for more deterministic responses
- **Max Output Tokens**: 4096 tokens
- **Timeout**: 120 seconds for API calls
- **History Truncation**: Enabled to handle context limits

## Troubleshooting

### Common Issues

1. **Cannot connect to Ollama**
   ```
   Error: Cannot connect to Ollama
   ```
   **Solution**:
   - Ensure Ollama is running: `ollama serve`
   - Check if port 11434 is accessible
   - If Ollama is on a different machine, update the `ollama_base_url` in `config.toml`

2. **Models not found**
   ```
   Warning: Neither deepseek-coder-v2:latest nor deepseek-r1:14b found
   ```
   **Solution**:
   ```bash
   ollama pull deepseek-coder-v2:latest
   ollama pull deepseek-r1:14b
   ```

3. **Docker connection issues**
   ```
   Error: Docker is not running
   ```
   **Solution**: Start Docker Desktop or Docker daemon

4. **Port 3000 already in use**
   **Solution**: Stop other services using port 3000 or modify the port in `docker-compose.ollama.yml`

### Logs and Debugging

- **View OpenHands logs**: `./start-ollama.sh logs`
- **Debug mode**: Already enabled in `config.toml` (`debug = true`)
- **Container logs**: `docker logs openhands-ollama`

### Performance Optimization

1. **Model Loading**: Keep Ollama running to avoid model reload delays
2. **Memory**: Ensure sufficient RAM for both Ollama models and OpenHands
3. **GPU**: If available, configure Ollama to use GPU acceleration

## Customization

### Changing Models

To use different models, update `config.toml`:

```toml
[llm]
model = "ollama/your-model-name"
```

### Network Configuration

If Ollama is running on a different machine:

```toml
[llm]
ollama_base_url = "http://YOUR_OLLAMA_HOST:11434"
```

### Adding More Models

Add additional model configurations:

```toml
[llm.custom-model]
model = "ollama/custom-model"
ollama_base_url = "http://host.docker.internal:11434"
temperature = 0.2
max_output_tokens = 2048
```

## Security Considerations

- The setup uses `host.docker.internal` to access the host machine
- Ollama API is accessed without authentication (default Ollama setup)
- Consider firewall rules if exposing to external networks

## Support

If you encounter issues:

1. Check the logs: `./start-ollama.sh logs`
2. Verify Ollama connectivity: `curl http://localhost:11434/api/tags`
3. Ensure models are loaded: `ollama list`
4. Check Docker status: `docker ps`

## MCP (Model Context Protocol) Servers

OpenHands supports MCP servers that provide additional tools and capabilities. **MCP is completely optional** - OpenHands works perfectly without it.

If you see "No MCP servers are currently configured" in the interface, this is normal and not an error. You can:

- **Ignore it**: OpenHands works great without MCP servers
- **Configure MCP**: See `MCP_SETUP.md` for detailed instructions on adding useful tools like file operations, git integration, web search, and more

Common useful MCP servers include:
- **Filesystem**: Enhanced file operations
- **Git**: Advanced version control
- **Time**: Current time and date functions
- **Web Search**: Real-time search capabilities (requires API key)

## File Structure

```
OpenHands/
├── config.toml                 # Main configuration file
├── docker-compose.ollama.yml   # Docker Compose for Ollama setup
├── start-ollama.sh            # Automated setup script
├── check-ollama-setup.sh      # Health check script
├── OLLAMA_SETUP.md            # This guide
├── MCP_SETUP.md               # MCP servers configuration guide
├── QUICK_REFERENCE.md         # Quick command reference
└── workspace/                 # Your working directory
```

---

**Happy coding with OpenHands and DeepSeek! 🚀**
