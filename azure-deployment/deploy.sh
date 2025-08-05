#!/bin/bash

# OpenHands Azure Deployment Script
# This script deploys OpenHands to Azure using either Container Instances or Container Apps

set -e

# Default values
RESOURCE_GROUP="openhands-rg"
LOCATION="eastus"
DEPLOYMENT_TYPE="container-apps"  # Options: container-instances, container-apps
IMAGE_TAG="latest"
APP_NAME="openhands-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Deploy OpenHands to Azure"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group NAME    Resource group name (default: $RESOURCE_GROUP)"
    echo "  -l, --location LOCATION      Azure region (default: $LOCATION)"
    echo "  -t, --type TYPE              Deployment type: container-instances or container-apps (default: $DEPLOYMENT_TYPE)"
    echo "  -i, --image-tag TAG          Docker image tag (default: $IMAGE_TAG)"
    echo "  -n, --name NAME              Application name (default: $APP_NAME)"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Required environment variables:"
    echo "  OPENAI_API_KEY              Your OpenAI API key"
    echo "  GITHUB_TOKEN                Your GitHub token (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 --type container-apps --location westus2"
    echo "  $0 -g my-rg -t container-instances -i v1.0.0"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -i|--image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -n|--name)
            APP_NAME="$2"
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

# Validate deployment type
if [[ "$DEPLOYMENT_TYPE" != "container-instances" && "$DEPLOYMENT_TYPE" != "container-apps" ]]; then
    print_error "Invalid deployment type: $DEPLOYMENT_TYPE"
    print_error "Valid options: container-instances, container-apps"
    exit 1
fi

# Check if required tools are installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    print_error "You are not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Check required environment variables
if [[ -z "$OPENAI_API_KEY" ]]; then
    print_error "OPENAI_API_KEY environment variable is required"
    print_info "Please set it with: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

# Set default GitHub token if not provided
if [[ -z "$GITHUB_TOKEN" ]]; then
    print_warning "GITHUB_TOKEN not set. GitHub integration will be disabled."
    GITHUB_TOKEN=""
fi

print_info "Starting OpenHands deployment to Azure..."
print_info "Resource Group: $RESOURCE_GROUP"
print_info "Location: $LOCATION"
print_info "Deployment Type: $DEPLOYMENT_TYPE"
print_info "Image Tag: $IMAGE_TAG"
print_info "App Name: $APP_NAME"

# Create resource group if it doesn't exist
print_info "Creating resource group if it doesn't exist..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
print_success "Resource group '$RESOURCE_GROUP' is ready"

# Deploy based on type
if [[ "$DEPLOYMENT_TYPE" == "container-instances" ]]; then
    print_info "Deploying using Azure Container Instances..."
    
    DEPLOYMENT_NAME="openhands-aci-$(date +%s)"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$(dirname "$0")/azure-container-instance.json" \
        --parameters \
            containerGroupName="$APP_NAME" \
            imageTag="$IMAGE_TAG" \
            openaiApiKey="$OPENAI_API_KEY" \
            githubToken="$GITHUB_TOKEN" \
        --name "$DEPLOYMENT_NAME" \
        --output table
    
    # Get the public IP
    PUBLIC_IP=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$DEPLOYMENT_NAME" \
        --query 'properties.outputs.containerIPv4Address.value' \
        --output tsv)
    
    print_success "Deployment completed successfully!"
    print_info "Application URL: http://$PUBLIC_IP:3000"
    
elif [[ "$DEPLOYMENT_TYPE" == "container-apps" ]]; then
    print_info "Deploying using Azure Container Apps..."
    
    # Register the Microsoft.App provider if not already registered
    print_info "Registering Microsoft.App provider..."
    az provider register --namespace Microsoft.App --wait
    
    DEPLOYMENT_NAME="openhands-ca-$(date +%s)"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$(dirname "$0")/azure-container-apps.json" \
        --parameters \
            containerAppName="$APP_NAME" \
            containerAppEnvironmentName="${APP_NAME}-env" \
            imageTag="$IMAGE_TAG" \
            openaiApiKey="$OPENAI_API_KEY" \
            githubToken="$GITHUB_TOKEN" \
        --name "$DEPLOYMENT_NAME" \
        --output table
    
    # Get the application URL
    APP_URL=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$DEPLOYMENT_NAME" \
        --query 'properties.outputs.containerAppUrl.value' \
        --output tsv)
    
    print_success "Deployment completed successfully!"
    print_info "Application URL: $APP_URL"
fi

print_success "OpenHands is now running on Azure!"
print_info "Resource requirements: 2 vCPUs, 4GB RAM"
print_info "To delete the deployment, run: az group delete --name $RESOURCE_GROUP"