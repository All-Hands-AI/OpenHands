#!/bin/bash

# Azure VM Deployment Validation Script for OpenHands
# This script validates the VM deployment and checks OpenHands status

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group NAME    Resource group name (default: $RESOURCE_GROUP)"
    echo "  -n, --vm-name NAME           VM name (default: $VM_NAME)"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 --resource-group my-rg --vm-name my-vm"
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

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    print_error "You are not logged in to Azure. Please run 'az login' first."
    exit 1
fi

print_status "Validating OpenHands VM deployment..."
print_status "Resource Group: $RESOURCE_GROUP"
print_status "VM Name: $VM_NAME"
echo ""

# Check if resource group exists
print_status "Checking resource group..."
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_success "Resource group '$RESOURCE_GROUP' exists"
else
    print_error "Resource group '$RESOURCE_GROUP' does not exist"
    exit 1
fi

# Check if VM exists
print_status "Checking virtual machine..."
if az vm show --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" &> /dev/null; then
    print_success "VM '$VM_NAME' exists"
else
    print_error "VM '$VM_NAME' does not exist in resource group '$RESOURCE_GROUP'"
    exit 1
fi

# Get VM status
print_status "Checking VM power state..."
VM_STATUS=$(az vm get-instance-view --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --query 'instanceView.statuses[1].displayStatus' -o tsv)
if [[ "$VM_STATUS" == "VM running" ]]; then
    print_success "VM is running"
else
    print_warning "VM status: $VM_STATUS"
    if [[ "$VM_STATUS" != "VM running" ]]; then
        print_status "Starting VM..."
        az vm start --resource-group "$RESOURCE_GROUP" --name "$VM_NAME"
        print_success "VM started"
    fi
fi

# Get VM connection information
print_status "Retrieving VM connection information..."
PUBLIC_IP=$(az vm show --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --show-details --query 'publicIps' -o tsv)
FQDN=$(az vm show --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --show-details --query 'fqdns' -o tsv)
ADMIN_USERNAME=$(az vm show --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --query 'osProfile.adminUsername' -o tsv)

if [[ -n "$FQDN" ]]; then
    HOSTNAME="$FQDN"
elif [[ -n "$PUBLIC_IP" ]]; then
    HOSTNAME="$PUBLIC_IP"
else
    print_error "Could not retrieve VM hostname or IP address"
    exit 1
fi

print_success "VM connection details retrieved"
echo "  Hostname: $HOSTNAME"
echo "  Admin Username: $ADMIN_USERNAME"
echo "  SSH Command: ssh $ADMIN_USERNAME@$HOSTNAME"
echo "  OpenHands URL: http://$HOSTNAME:3000"
echo ""

# Test SSH connectivity (optional)
print_status "Testing SSH connectivity (this may take a moment)..."
if timeout 10 ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$ADMIN_USERNAME@$HOSTNAME" 'echo "SSH connection successful"' &> /dev/null; then
    print_success "SSH connection successful"
    
    # Check Docker status
    print_status "Checking Docker status on VM..."
    DOCKER_STATUS=$(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$ADMIN_USERNAME@$HOSTNAME" 'sudo systemctl is-active docker' 2>/dev/null || echo "unknown")
    if [[ "$DOCKER_STATUS" == "active" ]]; then
        print_success "Docker is running"
    else
        print_warning "Docker status: $DOCKER_STATUS"
    fi
    
    # Check OpenHands container status
    print_status "Checking OpenHands container status..."
    CONTAINER_STATUS=$(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$ADMIN_USERNAME@$HOSTNAME" 'docker ps --filter name=openhands --format "{{.Status}}"' 2>/dev/null || echo "not found")
    if [[ "$CONTAINER_STATUS" == *"Up"* ]]; then
        print_success "OpenHands container is running"
        echo "  Container Status: $CONTAINER_STATUS"
    else
        print_warning "OpenHands container status: $CONTAINER_STATUS"
        print_status "Attempting to start OpenHands..."
        ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$ADMIN_USERNAME@$HOSTNAME" 'cd ~/openhands && docker-compose up -d' &> /dev/null
        sleep 5
        CONTAINER_STATUS=$(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$ADMIN_USERNAME@$HOSTNAME" 'docker ps --filter name=openhands --format "{{.Status}}"' 2>/dev/null || echo "not found")
        if [[ "$CONTAINER_STATUS" == *"Up"* ]]; then
            print_success "OpenHands container started successfully"
        else
            print_error "Failed to start OpenHands container"
        fi
    fi
else
    print_warning "SSH connection failed or timed out"
    print_status "This could be due to:"
    echo "  - VM is still booting up"
    echo "  - SSH key authentication not configured"
    echo "  - Network security group blocking SSH"
    echo "  - VM is not fully provisioned yet"
fi

# Test HTTP connectivity to OpenHands
print_status "Testing OpenHands web interface..."
if timeout 10 curl -s -o /dev/null -w "%{http_code}" "http://$HOSTNAME:3000" | grep -q "200\|302\|404"; then
    print_success "OpenHands web interface is accessible"
else
    print_warning "OpenHands web interface is not accessible yet"
    print_status "This is normal if the VM was just deployed. Please wait a few minutes."
fi

echo ""
print_success "=== Validation Complete ==="
echo "VM Hostname: $HOSTNAME"
echo "SSH Command: ssh $ADMIN_USERNAME@$HOSTNAME"
echo "OpenHands URL: http://$HOSTNAME:3000"
echo ""
print_status "If OpenHands is not accessible, please wait a few minutes for the container to start."
print_status "You can check the status by SSH'ing into the VM and running: docker ps"
echo ""