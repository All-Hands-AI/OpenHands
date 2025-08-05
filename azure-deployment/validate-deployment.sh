#!/bin/bash

# OpenHands Azure Deployment Validation Script
# This script helps validate that your Azure deployment is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP="openhands-rg"
APP_NAME="openhands-app"
DEPLOYMENT_TYPE="container-apps"
TIMEOUT=300  # 5 minutes

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group NAME    Resource group name (default: openhands-rg)"
    echo "  -n, --name NAME              Application name (default: openhands-app)"
    echo "  -t, --type TYPE              Deployment type: container-instances or container-apps (default: container-apps)"
    echo "  -T, --timeout SECONDS        Timeout for health checks (default: 300)"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Validate default deployment"
    echo "  $0 --resource-group my-rg --name my-app    # Validate custom deployment"
    echo "  $0 --type container-instances               # Validate Container Instances deployment"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -n|--name)
            APP_NAME="$2"
            shift 2
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -T|--timeout)
            TIMEOUT="$2"
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
if [[ "$DEPLOYMENT_TYPE" != "container-apps" && "$DEPLOYMENT_TYPE" != "container-instances" ]]; then
    print_error "Invalid deployment type: $DEPLOYMENT_TYPE"
    print_error "Must be either 'container-apps' or 'container-instances'"
    exit 1
fi

print_status "Validating OpenHands Azure deployment..."
print_status "Resource Group: $RESOURCE_GROUP"
print_status "Application Name: $APP_NAME"
print_status "Deployment Type: $DEPLOYMENT_TYPE"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    print_error "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

print_success "Azure CLI is installed"

# Check if user is logged in
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

print_success "Logged in to Azure"

# Check if resource group exists
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_error "Resource group '$RESOURCE_GROUP' does not exist."
    exit 1
fi

print_success "Resource group '$RESOURCE_GROUP' exists"

# Validate deployment based on type
if [[ "$DEPLOYMENT_TYPE" == "container-apps" ]]; then
    print_status "Validating Container Apps deployment..."
    
    # Check if container app exists
    if ! az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_error "Container App '$APP_NAME' does not exist in resource group '$RESOURCE_GROUP'."
        exit 1
    fi
    
    print_success "Container App '$APP_NAME' exists"
    
    # Get container app status
    STATUS=$(az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.provisioningState" -o tsv)
    if [[ "$STATUS" != "Succeeded" ]]; then
        print_warning "Container App provisioning state: $STATUS"
        if [[ "$STATUS" == "Failed" ]]; then
            print_error "Container App deployment failed"
            exit 1
        fi
    else
        print_success "Container App is successfully provisioned"
    fi
    
    # Get the FQDN
    FQDN=$(az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
    if [[ -z "$FQDN" ]]; then
        print_error "Could not retrieve FQDN for Container App"
        exit 1
    fi
    
    APP_URL="https://$FQDN"
    
else
    print_status "Validating Container Instances deployment..."
    
    # Check if container group exists
    if ! az container show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_error "Container Instance '$APP_NAME' does not exist in resource group '$RESOURCE_GROUP'."
        exit 1
    fi
    
    print_success "Container Instance '$APP_NAME' exists"
    
    # Get container instance status
    STATUS=$(az container show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "containers[0].instanceView.currentState.state" -o tsv)
    if [[ "$STATUS" != "Running" ]]; then
        print_warning "Container Instance state: $STATUS"
        if [[ "$STATUS" == "Failed" || "$STATUS" == "Terminated" ]]; then
            print_error "Container Instance is not running properly"
            # Show recent logs
            print_status "Recent logs:"
            az container logs --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --tail 20 || true
            exit 1
        fi
    else
        print_success "Container Instance is running"
    fi
    
    # Get the public IP
    PUBLIC_IP=$(az container show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "ipAddress.ip" -o tsv)
    if [[ -z "$PUBLIC_IP" ]]; then
        print_error "Could not retrieve public IP for Container Instance"
        exit 1
    fi
    
    APP_URL="http://$PUBLIC_IP:3000"
fi

print_success "Application URL: $APP_URL"

# Test application health
print_status "Testing application health..."
print_status "Waiting for application to be ready (timeout: ${TIMEOUT}s)..."

START_TIME=$(date +%s)
HEALTH_CHECK_PASSED=false

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [[ $ELAPSED -gt $TIMEOUT ]]; then
        print_error "Health check timed out after ${TIMEOUT} seconds"
        break
    fi
    
    # Try to connect to the application
    if curl -s --max-time 10 "$APP_URL" > /dev/null 2>&1; then
        print_success "Application is responding to HTTP requests"
        HEALTH_CHECK_PASSED=true
        break
    fi
    
    print_status "Waiting for application to respond... (${ELAPSED}s elapsed)"
    sleep 10
done

if [[ "$HEALTH_CHECK_PASSED" == "true" ]]; then
    print_success "\n=== VALIDATION SUCCESSFUL ==="
    print_success "Your OpenHands deployment is working correctly!"
    print_success "Application URL: $APP_URL"
    echo ""
    print_status "Next steps:"
    echo "  1. Open $APP_URL in your browser"
    echo "  2. Verify that the OpenHands interface loads correctly"
    echo "  3. Test creating a new conversation"
    echo "  4. Check that the AI assistant responds properly"
    echo ""
else
    print_error "\n=== VALIDATION FAILED ==="
    print_error "Your OpenHands deployment is not responding properly."
    echo ""
    print_status "Troubleshooting steps:"
    echo "  1. Check application logs:"
    if [[ "$DEPLOYMENT_TYPE" == "container-apps" ]]; then
        echo "     az containerapp logs show --name $APP_NAME --resource-group $RESOURCE_GROUP --follow"
    else
        echo "     az container logs --name $APP_NAME --resource-group $RESOURCE_GROUP --follow"
    fi
    echo "  2. Verify environment variables are set correctly"
    echo "  3. Check that OPENAI_API_KEY is valid"
    echo "  4. Ensure the container image is accessible"
    echo ""
    exit 1
fi