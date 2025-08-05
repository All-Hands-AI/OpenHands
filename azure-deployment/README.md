# OpenHands Azure Deployment

This directory contains Azure deployment templates and scripts to deploy OpenHands to Microsoft Azure. The deployment meets the minimum requirements of **4GB RAM and 2 vCPUs**.

## Deployment Options

We provide three deployment options:

1. **Azure Container Instances (ACI)** - Simple, serverless container deployment
2. **Azure Container Apps** - Managed container platform with auto-scaling capabilities
3. **Azure Virtual Machine (VM)** - Full control VM deployment with Docker (8GB RAM, 4 vCPUs)

## Prerequisites

### Required Tools
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and configured
- An active Azure subscription
- OpenAI API key for LLM integration

### Required Environment Variables
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `GITHUB_TOKEN` - Your GitHub personal access token (optional, for GitHub integration)

## Quick Start

### 1. Login to Azure
```bash
az login
```

### 2. Set Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export GITHUB_TOKEN="your-github-token-here"  # Optional
```

### 3. Deploy Using the Script
```bash
# Deploy using Container Apps (recommended)
./deploy.sh --type container-apps

# Or deploy using Container Instances
./deploy.sh --type container-instances

# Or deploy using Virtual Machine with Docker
./deploy-vm.sh --ssh-key-path ~/.ssh/id_rsa.pub
```

## Deployment Script Options

The `deploy.sh` script supports the following options:

```bash
./deploy.sh [OPTIONS]

Options:
  -g, --resource-group NAME    Resource group name (default: openhands-rg)
  -l, --location LOCATION      Azure region (default: eastus)
  -t, --type TYPE              Deployment type: container-instances or container-apps (default: container-apps)
  -i, --image-tag TAG          Docker image tag (default: latest)
  -n, --name NAME              Application name (default: openhands-app)
  -h, --help                   Show help message
```

### Examples

```bash
# Deploy to West US 2 with custom resource group
./deploy.sh --resource-group my-openhands --location westus2

# Deploy specific version using Container Instances
./deploy.sh --type container-instances --image-tag v1.0.0

# Deploy with custom app name
./deploy.sh --name my-openhands-instance
```

## Manual Deployment

If you prefer to deploy manually using Azure CLI:

### Container Apps Deployment

```bash
# Create resource group
az group create --name openhands-rg --location eastus

# Register the Container Apps provider
az provider register --namespace Microsoft.App --wait

# Deploy using ARM template
az deployment group create \
  --resource-group openhands-rg \
  --template-file azure-container-apps.json \
  --parameters \
    containerAppName=openhands-app \
    openaiApiKey="$OPENAI_API_KEY" \
    githubToken="$GITHUB_TOKEN"
```

### Container Instances Deployment

```bash
# Create resource group
az group create --name openhands-rg --location eastus

# Deploy using ARM template
az deployment group create \
  --resource-group openhands-rg \
  --template-file azure-container-instance.json \
  --parameters \
    containerGroupName=openhands-app \
    openaiApiKey="$OPENAI_API_KEY" \
    githubToken="$GITHUB_TOKEN"
```

## Resource Specifications

Both deployment options are configured with:
- **CPU**: 2.0 cores
- **Memory**: 4GB RAM
- **Storage**: Ephemeral storage for workspace
- **Networking**: Public IP with port 3000 exposed

## Configuration

### Environment Variables

The deployment includes the following pre-configured environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `LLM_MODEL` | OpenAI model to use | `gpt-4o` |
| `LLM_API_KEY` | OpenAI API key | From parameter |
| `SANDBOX_RUNTIME_CONTAINER_IMAGE` | Runtime container image | `ghcr.io/all-hands-ai/runtime:0.51-nikolaik` |
| `WORKSPACE_BASE` | Base workspace directory | `/workspace` |
| `WORKSPACE_MOUNT_PATH` | Workspace mount path | `/workspace` |
| `RUN_AS_OPENHANDS` | Run as openhands user | `true` |
| `SANDBOX_USER_ID` | User ID for sandbox | `1000` |
| `GITHUB_TOKEN` | GitHub access token | From parameter |
| `RUNTIME` | Runtime type | `docker` |

### Customizing the Deployment

To customize the deployment, you can:

1. **Modify the ARM templates** (`azure-container-apps.json` or `azure-container-instance.json`)
2. **Update environment variables** in the templates
3. **Change resource specifications** (CPU/memory) in the templates
4. **Add additional volumes** or configuration as needed

## Scaling (Container Apps Only)

The Container Apps deployment includes auto-scaling configuration:
- **Minimum replicas**: 1
- **Maximum replicas**: 3
- **Scaling rule**: HTTP-based scaling (10 concurrent requests per instance)

## Monitoring and Logs

### Container Apps
- Logs are automatically sent to Azure Log Analytics
- Use Azure Monitor to view application metrics and logs
- Access logs via: `az containerapp logs show --name openhands-app --resource-group openhands-rg`

### Container Instances
- View logs via: `az container logs --name openhands-app --resource-group openhands-rg`
- Monitor via Azure Portal or Azure CLI

## Security Considerations

1. **API Keys**: Stored as secure parameters/secrets in Azure
2. **Network**: Public IP with HTTPS (Container Apps) or HTTP (Container Instances)
3. **Container Security**: Uses official OpenHands container images
4. **Access Control**: Configure Azure RBAC as needed

## Troubleshooting

### Common Issues

1. **Deployment fails with provider not registered**
   ```bash
   az provider register --namespace Microsoft.App --wait
   ```

2. **Container fails to start**
   - Check environment variables are set correctly
   - Verify OpenAI API key is valid
   - Check container logs for specific errors

3. **Application not accessible**
   - Verify the public IP/FQDN from deployment output
   - Check Azure Network Security Groups if using custom networking
   - Ensure port 3000 is accessible

### Getting Logs

```bash
# Container Apps
az containerapp logs show --name openhands-app --resource-group openhands-rg --follow

# Container Instances
az container logs --name openhands-app --resource-group openhands-rg --follow
```

### Checking Deployment Status

```bash
# List deployments
az deployment group list --resource-group openhands-rg --output table

# Show specific deployment
az deployment group show --resource-group openhands-rg --name <deployment-name>
```

## Cost Optimization

### Container Apps
- Scales to zero when not in use (if configured)
- Pay-per-use pricing model
- Automatic resource optimization

### Container Instances
- Pay-per-second billing
- No minimum charges
- Good for development/testing

## Cleanup

To remove all deployed resources:

```bash
az group delete --name openhands-rg --yes --no-wait
```

## Support

For issues related to:
- **OpenHands application**: Check the main [OpenHands repository](https://github.com/All-Hands-AI/OpenHands)
- **Azure deployment**: Review Azure documentation or create an issue in the repository
- **Azure services**: Consult [Azure documentation](https://docs.microsoft.com/en-us/azure/)

## Virtual Machine Deployment

The VM deployment option provides the most control and resources, deploying OpenHands on an Ubuntu 20.04 VM with Docker.

### VM Specifications
- **Default VM Size**: Standard_B4ms (4 vCPUs, 16GB RAM)
- **Operating System**: Ubuntu 20.04 LTS
- **Docker**: Automatically installed and configured
- **OpenHands**: Deployed as Docker container with auto-restart

### VM Deployment Usage

```bash
# Basic deployment with SSH key
./deploy-vm.sh --ssh-key-path ~/.ssh/id_rsa.pub

# Deployment with password authentication
./deploy-vm.sh --auth-type password --password 'YourSecurePassword123!'

# Custom configuration
./deploy-vm.sh \
  --resource-group my-openhands-rg \
  --vm-name my-openhands-vm \
  --location westus2 \
  --vm-size Standard_B2s \
  --ssh-key-path ~/.ssh/id_rsa.pub
```

### VM Deployment Options

| Option | Description | Default |
|--------|-------------|----------|
| `--resource-group` | Azure resource group name | `my-openhands` |
| `--vm-name` | Virtual machine name | `openhands-vm` |
| `--location` | Azure region | `eastus` |
| `--admin-username` | VM admin username | `azureuser` |
| `--vm-size` | VM size (see Azure VM sizes) | `Standard_B4ms` |
| `--image-tag` | Docker image tag | `latest` |
| `--auth-type` | Authentication type (`sshPublicKey` or `password`) | `sshPublicKey` |
| `--ssh-key-path` | Path to SSH public key file | Required for SSH auth |
| `--password` | Admin password | Required for password auth |

### Recommended VM Sizes

| VM Size | vCPUs | RAM | Use Case |
|---------|-------|-----|----------|
| `Standard_B2s` | 2 | 4GB | Light development |
| `Standard_B4ms` | 4 | 16GB | **Recommended** - General use |
| `Standard_D4s_v3` | 4 | 16GB | High performance |
| `Standard_D8s_v3` | 8 | 32GB | Heavy workloads |

### VM Post-Deployment

After deployment:
1. **SSH Access**: Use the provided SSH command to connect
2. **OpenHands URL**: Access via the provided URL (port 3000)
3. **Docker Management**: Use `docker ps`, `docker logs openhands` for monitoring
4. **Auto-restart**: OpenHands automatically starts on VM boot

### VM Management Commands

```bash
# SSH into the VM
ssh azureuser@your-vm-hostname.region.cloudapp.azure.com

# Check OpenHands status
docker ps
docker logs openhands

# Restart OpenHands
cd ~/openhands
docker-compose restart

# Update OpenHands
cd ~/openhands
docker-compose pull
docker-compose up -d
```

## Contributing

To improve these deployment templates:
1. Fork the repository
2. Make your changes
3. Test the deployment
4. Submit a pull request

## License

These deployment templates are provided under the same license as the OpenHands project.