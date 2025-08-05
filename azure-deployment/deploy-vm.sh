#!/bin/bash

# Azure VM Deployment Script for OpenHands
# This script deploys OpenHands on an Azure VM with Docker

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
RESOURCE_GROUP="my-openhands"
VM_NAME="openhands-vm"
LOCATION="eastus"
ADMIN_USERNAME="azureuser"
VM_SIZE="Standard_B4ms"  # 4 vCPUs, 16GB RAM
IMAGE_TAG="latest"
AUTH_TYPE="sshPublicKey"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group NAME    Resource group name (default: $RESOURCE_GROUP)"
    echo "  -n, --vm-name NAME           VM name (default: $VM_NAME)"
    echo "  -l, --location LOCATION      Azure region (default: $LOCATION)"
    echo "  -u, --admin-username USER    Admin username (default: $ADMIN_USERNAME)"
    echo "  -s, --vm-size SIZE           VM size (default: $VM_SIZE)"
    echo "  -t, --image-tag TAG          Docker image tag (default: $IMAGE_TAG)"
    echo "  -a, --auth-type TYPE         Authentication type: sshPublicKey or password (default: $AUTH_TYPE)"
    echo "  -k, --ssh-key-path PATH      Path to SSH public key file (required for SSH auth)"
    echo "  -p, --password PASSWORD      Admin password (required for password auth)"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Environment variables required:"
    echo "  OPENAI_API_KEY              OpenAI API key"
    echo "  GITHUB_TOKEN                GitHub personal access token"
    echo ""
    echo "Examples:"
    echo "  # Deploy with SSH key authentication"
    echo "  $0 --ssh-key-path ~/.ssh/id_rsa.pub"
    echo ""
    echo "  # Deploy with password authentication"
    echo "  $0 --auth-type password --password 'YourSecurePassword123!'"
    echo ""
    echo "  # Deploy with custom settings"
    echo "  $0 --resource-group my-rg --vm-name my-vm --location westus2 --vm-size Standard_B2s --ssh-key-path ~/.ssh/id_rsa.pub"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -n|--vm-name)
            VM_NAME="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -u|--admin-username)
            ADMIN_USERNAME="$2"
            shift 2
            ;;
        -s|--vm-size)
            VM_SIZE="$2"
            shift 2
            ;;
        -t|--image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -a|--auth-type)
            AUTH_TYPE="$2"
            shift 2
            ;;
        -k|--ssh-key-path)
            SSH_KEY_PATH="$2"
            shift 2
            ;;
        -p|--password)
            ADMIN_PASSWORD="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required environment variables
if [[ -z "$OPENAI_API_KEY" ]]; then
    print_error "OPENAI_API_KEY environment variable is required"
    exit 1
fi

if [[ -z "$GITHUB_TOKEN" ]]; then
    print_error "GITHUB_TOKEN environment variable is required"
    exit 1
fi

# Validate authentication parameters
if [[ "$AUTH_TYPE" == "sshPublicKey" ]]; then
    if [[ -z "$SSH_KEY_PATH" ]]; then
        print_error "SSH key path is required for SSH authentication"
        print_error "Use --ssh-key-path to specify the path to your public key"
        exit 1
    fi
    if [[ ! -f "$SSH_KEY_PATH" ]]; then
        print_error "SSH key file not found: $SSH_KEY_PATH"
        exit 1
    fi
    ADMIN_PASSWORD_OR_KEY=$(cat "$SSH_KEY_PATH")
elif [[ "$AUTH_TYPE" == "password" ]]; then
    if [[ -z "$ADMIN_PASSWORD" ]]; then
        print_error "Password is required for password authentication"
        print_error "Use --password to specify the admin password"
        exit 1
    fi
    ADMIN_PASSWORD_OR_KEY="$ADMIN_PASSWORD"
else
    print_error "Invalid authentication type: $AUTH_TYPE"
    print_error "Must be either 'sshPublicKey' or 'password'"
    exit 1
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    print_error "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    print_error "You are not logged in to Azure. Please run 'az login' first."
    exit 1
fi

print_status "Starting Azure VM deployment for OpenHands..."
print_status "Resource Group: $RESOURCE_GROUP"
print_status "VM Name: $VM_NAME"
print_status "Location: $LOCATION"
print_status "VM Size: $VM_SIZE"
print_status "Admin Username: $ADMIN_USERNAME"
print_status "Authentication Type: $AUTH_TYPE"
print_status "Image Tag: $IMAGE_TAG"

# Create resource group if it doesn't exist
print_status "Checking if resource group '$RESOURCE_GROUP' exists..."
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_status "Creating resource group '$RESOURCE_GROUP' in '$LOCATION'..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    print_success "Resource group created successfully"
else
    print_status "Resource group '$RESOURCE_GROUP' already exists"
fi

# Deploy the VM using ARM template
print_status "Deploying VM with OpenHands..."
DEPLOYMENT_NAME="openhands-vm-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "azure-vm.json" \
    --parameters \
        vmName="$VM_NAME" \
        adminUsername="$ADMIN_USERNAME" \
        authenticationType="$AUTH_TYPE" \
        adminPasswordOrKey="$ADMIN_PASSWORD_OR_KEY" \
        vmSize="$VM_SIZE" \
        location="$LOCATION" \
        openaiApiKey="$OPENAI_API_KEY" \
        githubToken="$GITHUB_TOKEN" \
        imageTag="$IMAGE_TAG" \
    --name "$DEPLOYMENT_NAME"

if [[ $? -eq 0 ]]; then
    print_success "VM deployment completed successfully!"
    
    # Get deployment outputs
    print_status "Retrieving deployment information..."
    HOSTNAME=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query 'properties.outputs.hostname.value' -o tsv)
    SSH_COMMAND=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query 'properties.outputs.sshCommand.value' -o tsv)
    OPENHANDS_URL=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query 'properties.outputs.openhandsUrl.value' -o tsv)
    
    echo ""
    print_success "=== Deployment Complete ==="
    echo "VM Hostname: $HOSTNAME"
    echo "SSH Command: $SSH_COMMAND"
    echo "OpenHands URL: $OPENHANDS_URL"
    echo ""
    print_status "Note: It may take a few minutes for OpenHands to start after the VM boots."
    print_status "You can check the status by SSH'ing into the VM and running: docker ps"
    echo ""
else
    print_error "VM deployment failed!"
    exit 1
fi