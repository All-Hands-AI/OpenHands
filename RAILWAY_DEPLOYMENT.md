# OpenHands Railway Deployment Guide

This guide explains how to deploy OpenHands to Railway.com with Docker-in-Docker (DinD) support.

## Prerequisites

1. A Railway.com account
2. Railway CLI installed (optional, for local testing)
3. Your OpenHands repository forked and accessible

## Files Created for Railway Deployment

1. **`Dockerfile.railway`** - Railway-optimized Dockerfile with E2B runtime support
2. **`railway.toml`** - Railway service configuration
3. **`RAILWAY_DEPLOYMENT.md`** - This deployment guide

## Deployment Steps

### Option 1: Deploy via Railway Dashboard (Recommended)

1. **Connect Repository**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `smishi204/OpenHands` repository

2. **Configure Build Settings**
   - Railway should automatically detect the `railway.toml` file
   - If not, manually set:
     - Build Command: `docker build -f Dockerfile.railway -t openhands .`
     - Start Command: `/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf`

3. **Set Environment Variables**
   The following environment variables are pre-configured in `railway.toml` but you may want to customize:

   **Required:**
   - `PORT` - Railway sets this automatically (DO NOT override)
   - `RUNTIME=e2b` - Uses E2B runtime (no Docker needed)
   - `e2b api key` - Your E2B API key (get from e2b.dev)

   **Required (LLM providers - choose one):**
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `ANTHROPIC_API_KEY` - Your Anthropic API key  
   - `GOOGLE_API_KEY` - Your Google API key

   **Optional:**
   - Add other LLM provider keys as needed

   **Important:** 
   - Do not set the `PORT` environment variable manually. Railway automatically assigns and manages ports.
   - You must set an E2B_API_KEY to use the E2B runtime. Sign up at https://e2b.dev for free API access.

4. **Deploy**
   - Click "Deploy" and wait for the build to complete
   - The service will be available at your Railway-provided URL

### Option 2: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

## Configuration Details

### E2B Runtime Setup

The `Dockerfile.railway` includes:
- E2B runtime configuration (no Docker daemon needed)
- Streamlined Python-based container
- Proper user and permission setup
- Health checks for Railway monitoring

### Resource Requirements

The deployment is configured for:
- **Memory**: 4GB RAM (minimum recommended)
- **CPU**: 2 vCPUs
- **Storage**: Persistent volumes for workspace and Docker data

### Networking

- **Port**: 3000 (configurable via PORT environment variable)
- **Health Check**: `/health` endpoint
- **CORS**: Configured for Railway domains

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | (auto-assigned) | Application port (set automatically by Railway) |
| `HOST` | `0.0.0.0` | Host binding |
| `RUNTIME` | `e2b` | Runtime type (E2B cloud sandboxes) |
| `E2B_API_KEY` | (required) | E2B API key for sandbox access |
| `LOG_ALL_EVENTS` | `true` | Enable comprehensive logging |
| `FILE_STORE` | `local` | File storage type |
| `FILE_STORE_PATH` | `/.openhands-state` | State storage path |

## LLM Provider Configuration

After deployment, you'll need to configure an LLM provider. Add one of these environment variables:

### OpenAI
```
OPENAI_API_KEY=your_openai_api_key
```

### Anthropic (Recommended)
```
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Google Gemini
```
GOOGLE_API_KEY=your_google_api_key
```

## Troubleshooting

### Common Issues

1. **Docker daemon not starting**
   - Check logs: `railway logs`
   - Ensure sufficient memory allocation (minimum 4GB)

2. **Runtime container pull failures**
   - The deployment will continue even if the runtime image pull fails initially
   - The image will be pulled on first use

3. **Permission issues**
   - The container runs with proper user management
   - Docker group permissions are automatically configured

4. **Memory issues**
   - Increase memory allocation in Railway dashboard
   - Monitor resource usage via `/server_info` endpoint

### Monitoring

- **Health Check**: `https://your-app.railway.app/health`
- **Server Info**: `https://your-app.railway.app/server_info`
- **Logs**: Available in Railway dashboard

## Security Considerations

1. **API Keys**: Store LLM API keys as Railway environment variables (encrypted)
2. **Network**: The service runs in Railway's secure environment
3. **Docker**: DinD is contained within the Railway container
4. **File Access**: Limited to mounted volumes

## Scaling and Performance

- **Vertical Scaling**: Increase memory/CPU in Railway dashboard
- **Horizontal Scaling**: Not recommended (OpenHands is designed for single-user use)
- **Storage**: Persistent volumes for workspace and Docker data

## Support

If you encounter issues:
1. Check Railway logs for error messages
2. Verify environment variables are set correctly
3. Ensure sufficient resources are allocated
4. Refer to OpenHands documentation for application-specific issues

## Cost Optimization

- Railway charges based on resource usage
- Consider scaling down resources during low usage periods
- Monitor usage via Railway dashboard
- Use Railway's sleep feature for development deployments