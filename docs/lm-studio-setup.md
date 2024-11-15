# LM-Studio Integration Guide

This guide explains how to set up and run OpenHands with LM-Studio for local LLM execution.

## Prerequisites

1. Install [LM-Studio](https://lmstudio.ai/)
2. Docker and Docker Compose
3. Python 3.10+

## Setup Instructions

1. **Configure LM-Studio**:
   - Launch LM-Studio
   - Load your desired models (you'll need at least 3 models):
     - One for the Supervisor Agent (port 1234)
     - One for OpenHands Instance 1 (port 1235)
     - One for OpenHands Instance 2 (port 1236)
   - For each model:
     - Click "Start Server"
     - Configure the port as listed above
     - Enable local inference

2. **Start OpenHands Services**:
   ```bash
   docker-compose -f docker-compose.lmstudio.yml up -d
   ```

This will start:
- Supervisor Agent on port 8000
- OpenHands Instance 1 on port 8001
- OpenHands Instance 2 on port 8002

## Usage

1. **Interact with the Supervisor**:
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Your task here"}'
   ```

2. **Monitor Logs**:
   ```bash
   docker-compose -f docker-compose.lmstudio.yml logs -f
   ```

## Architecture

- **Supervisor Agent**: Manages task delegation and OpenHands instance coordination
- **OpenHands Instances**: Execute specific tasks using dedicated LLM instances
- **LM-Studio**: Provides local LLM inference for each component

## Configuration

The system uses `config.lmstudio.toml` for configuration:
- Each component has its own LLM configuration
- Different ports are used to connect to different LM-Studio model servers
- Memory is enabled for conversation context retention

## Troubleshooting

1. **Connection Issues**:
   - Ensure LM-Studio servers are running on correct ports
   - Check Docker network connectivity
   - Verify port mappings in docker-compose file

2. **Model Loading**:
   - Each LM-Studio instance should load successfully
   - Monitor LM-Studio logs for errors
   - Ensure sufficient system resources

3. **API Errors**:
   - Check configuration file paths
   - Verify environment variables
   - Monitor Docker container logs
