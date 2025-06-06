# Local vLLM DeepSeek R1-0528 Deployment Guide

This guide provides instructions for deploying OpenHands with a local DeepSeek R1-0528 model using vLLM, eliminating the need for external API keys.

## Overview

This deployment provides:
- ✅ **No API Keys Required**: Completely local deployment
- ✅ **Cost-Effective**: No per-token charges
- ✅ **Privacy**: All data stays local
- ✅ **Offline Capable**: Works without internet connection
- ✅ **Full Control**: Complete control over model behavior

## Quick Start

### Option 1: Mock Server (Recommended for Testing)

For development and testing when GPU resources are limited:

```bash
# Start the local mock server
python local_deepseek_mock_server.py

# In another terminal, start OpenHands
cp config.local.toml.example config.toml
uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000
```

### Option 2: Full vLLM Deployment (Production)

For production deployment with actual model inference:

```bash
# Install vLLM
pip install vllm

# Start vLLM server with DeepSeek R1-0528
vllm serve "deepseek-ai/DeepSeek-R1-0528" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --trust-remote-code \
    --max-model-len 4096

# Configure OpenHands
cp config.local.toml.example config.toml
# Edit config.toml to use http://localhost:8000/v1

# Start OpenHands
uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000
```

## System Requirements

### Mock Server (Minimal)
- **CPU**: Any modern CPU
- **RAM**: 2GB minimum
- **Storage**: 1GB
- **GPU**: Not required

### Full vLLM Deployment
- **CPU**: 8+ cores recommended
- **RAM**: 32GB+ recommended
- **Storage**: 50GB+ for model storage
- **GPU**: 24GB+ VRAM (RTX 4090, A100, etc.)

## Configuration Files

### config.toml
```toml
[core]
workspace_base = "/tmp/openhands_workspace"
persist_sandbox = false
run_as_openhands = true
runtime = "docker"
sandbox_container_image = "ghcr.io/all-hands-ai/runtime:latest"
max_iterations = 100
max_budget_per_task = 10.0

[llm]
model = "deepseek-ai/DeepSeek-R1-0528"
api_key = "local-no-key-required"
base_url = "http://localhost:8000/v1"
```

## Available Servers

### 1. Mock Server (`local_deepseek_mock_server.py`)
- **Purpose**: Development and testing
- **Requirements**: Minimal (CPU only)
- **Features**: 
  - OpenAI-compatible API
  - Contextual responses
  - No GPU required
  - Instant startup

### 2. vLLM Server (`local_deepseek_server.py`)
- **Purpose**: Production deployment
- **Requirements**: GPU with sufficient VRAM
- **Features**:
  - Full model inference
  - High performance
  - Streaming support
  - Production ready

## API Endpoints

Both servers provide OpenAI-compatible endpoints:

- `GET /health` - Health check
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions
- `GET /stats` - Server statistics (mock server only)

## Testing the Deployment

### Test Local Server
```bash
# Test health
curl http://localhost:8000/health

# Test chat completion
curl -X POST "http://localhost:8000/v1/chat/completions" \
    -H "Content-Type: application/json" \
    --data '{
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ]
    }'
```

### Test OpenHands Integration
```bash
# Test OpenHands API
curl http://localhost:3000/health

# Test models endpoint
curl http://localhost:3000/api/options/models
```

## Troubleshooting

### Common Issues

1. **vLLM fails to start**
   - Check GPU memory availability
   - Verify CUDA installation
   - Try CPU-only mode: `--device cpu`

2. **OpenHands can't connect to local server**
   - Verify server is running on port 8000
   - Check firewall settings
   - Ensure base_url in config.toml is correct

3. **Out of memory errors**
   - Reduce `--gpu-memory-utilization`
   - Use smaller model variant
   - Enable CPU offloading

### Performance Optimization

1. **GPU Optimization**
   ```bash
   # Use tensor parallelism for multi-GPU
   vllm serve "deepseek-ai/DeepSeek-R1-0528" \
       --tensor-parallel-size 2 \
       --gpu-memory-utilization 0.8
   ```

2. **CPU Optimization**
   ```bash
   # CPU-only deployment
   vllm serve "deepseek-ai/DeepSeek-R1-0528" \
       --device cpu \
       --dtype float16
   ```

## Security Considerations

- Local deployment eliminates data privacy concerns
- No external API calls or data transmission
- All processing happens on local hardware
- Consider network security if exposing endpoints

## Monitoring and Logging

### Server Logs
```bash
# Monitor vLLM server
tail -f logs/vllm_server.log

# Monitor OpenHands backend
tail -f logs/backend.log

# Monitor mock server
tail -f logs/local_deepseek.log
```

### Performance Metrics
- GPU utilization: `nvidia-smi`
- Memory usage: `htop` or `free -h`
- Network traffic: `netstat -i`

## Advanced Configuration

### Custom Model Parameters
```bash
vllm serve "deepseek-ai/DeepSeek-R1-0528" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 8192 \
    --temperature 0.7 \
    --top-p 0.9 \
    --trust-remote-code
```

### Load Balancing
For high-availability deployments, consider:
- Multiple vLLM instances
- Load balancer (nginx, HAProxy)
- Health check monitoring

## Migration from External APIs

To migrate from external DeepSeek API:

1. **Backup current configuration**
   ```bash
   cp config.toml config.toml.backup
   ```

2. **Update configuration**
   ```bash
   # Change base_url from external to local
   sed -i 's|https://api.deepseek.com|http://localhost:8000/v1|g' config.toml
   sed -i 's|your-api-key|local-no-key-required|g' config.toml
   ```

3. **Test and validate**
   ```bash
   # Run integration tests
   python test_complete_deployment.py
   ```

## Support and Resources

- **Documentation**: See OPENHANDS_DEEPSEEK_DEPLOYMENT.md for full setup
- **Testing**: Use test_complete_deployment.py for validation
- **Diagnostics**: Run diagnose.sh for troubleshooting
- **Examples**: Check startup.sh for automated deployment

## License and Attribution

This deployment guide is part of the OpenHands project with DeepSeek R1-0528 integration.
- OpenHands: https://github.com/All-Hands-AI/OpenHands
- DeepSeek: https://github.com/deepseek-ai/DeepSeek-R1