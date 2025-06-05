#!/bin/bash
# install_deepseek.sh - Complete setup script for DeepSeek R1-0528

set -e

echo "DeepSeek R1-0528 Installation Script"
echo "===================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root for security reasons."
   echo "Please run as a regular user with sudo privileges."
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "centos"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Function to install system dependencies
install_system_deps() {
    local os_type=$(detect_os)
    
    echo "Installing system dependencies for $os_type..."
    
    case $os_type in
        "ubuntu")
            sudo apt-get update
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                git \
                wget \
                curl \
                htop \
                nvtop
            ;;
        "centos")
            sudo yum update -y
            sudo yum install -y \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                gcc-c++ \
                make \
                git \
                wget \
                curl \
                htop
            ;;
        "macos")
            if ! command_exists brew; then
                echo "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python git wget curl htop
            ;;
        *)
            echo "Unsupported OS. Please install dependencies manually:"
            echo "- Python 3.8+"
            echo "- pip"
            echo "- git"
            echo "- build tools"
            ;;
    esac
}

# Function to check NVIDIA drivers
check_nvidia() {
    echo "Checking NVIDIA drivers..."
    
    if command_exists nvidia-smi; then
        echo "✓ NVIDIA drivers found:"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    else
        echo "⚠ NVIDIA drivers not found. GPU acceleration will not be available."
        echo "To install NVIDIA drivers:"
        echo "Ubuntu: sudo apt install nvidia-driver-535"
        echo "CentOS: sudo yum install nvidia-driver"
        echo "Or download from: https://www.nvidia.com/drivers"
    fi
}

# Function to setup Python environment
setup_python_env() {
    echo "Setting up Python environment..."
    
    # Check Python version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "Python version: $python_version"
    
    # Create virtual environment
    echo "Creating virtual environment..."
    python3 -m venv deepseek_env
    
    # Activate environment
    source deepseek_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    echo "✓ Python environment ready"
}

# Function to install PyTorch with CUDA support
install_pytorch() {
    echo "Installing PyTorch with CUDA support..."
    
    if command_exists nvidia-smi; then
        # Install CUDA version
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        echo "✓ PyTorch with CUDA support installed"
    else
        # Install CPU version
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        echo "✓ PyTorch (CPU-only) installed"
    fi
}

# Function to install core dependencies
install_core_deps() {
    echo "Installing core dependencies..."
    
    pip install \
        transformers>=4.37.0 \
        accelerate>=0.26.0 \
        bitsandbytes>=0.42.0 \
        sentencepiece \
        protobuf \
        datasets \
        evaluate \
        scikit-learn \
        numpy \
        pandas \
        matplotlib \
        seaborn \
        jupyter \
        ipywidgets
    
    echo "✓ Core dependencies installed"
}

# Function to install optional dependencies
install_optional_deps() {
    echo "Installing optional dependencies..."
    
    # Flash Attention (if CUDA available)
    if command_exists nvidia-smi; then
        echo "Installing Flash Attention..."
        pip install flash-attn --no-build-isolation || echo "⚠ Flash Attention installation failed (optional)"
    fi
    
    # vLLM (if CUDA available)
    if command_exists nvidia-smi; then
        echo "Installing vLLM..."
        pip install vllm || echo "⚠ vLLM installation failed (optional)"
    fi
    
    # Web server dependencies
    pip install \
        fastapi \
        uvicorn \
        aiofiles \
        websockets \
        prometheus-client \
        psutil
    
    # Development tools
    pip install \
        black \
        isort \
        flake8 \
        mypy \
        pytest \
        pytest-asyncio
    
    echo "✓ Optional dependencies installed"
}

# Function to test installation
test_installation() {
    echo "Testing installation..."
    
    python3 -c "
import torch
import transformers
import accelerate

print(f'✓ PyTorch {torch.__version__}')
print(f'✓ Transformers {transformers.__version__}')
print(f'✓ Accelerate {accelerate.__version__}')

if torch.cuda.is_available():
    print(f'✓ CUDA {torch.version.cuda}')
    print(f'✓ GPU: {torch.cuda.get_device_name()}')
    print(f'✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
else:
    print('⚠ CUDA not available - CPU mode only')

print('✓ Installation test passed')
"
}

# Function to download model (optional)
download_model() {
    echo "Do you want to download the DeepSeek R1-0528 model now? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Downloading DeepSeek R1-0528 model..."
        echo "This will download ~50GB of data. Make sure you have enough space."
        
        python3 -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
print('Downloading tokenizer...')
tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-R1-0528', trust_remote_code=True)
print('✓ Tokenizer downloaded')
print('Note: Model will be downloaded on first use to save space.')
"
    else
        echo "Model will be downloaded automatically on first use."
    fi
}

# Function to print final instructions
print_instructions() {
    echo ""
    echo "🎉 DeepSeek R1-0528 installation completed!"
    echo "========================================"
    echo ""
    echo "To get started:"
    echo "1. Activate the environment: source deepseek_env/bin/activate"
    echo "2. Copy config/.env.example to .env and customize if needed"
    echo "3. Run basic example: python examples/basic_usage.py"
    echo "4. Run memory-optimized example: python examples/memory_optimized.py"
    echo ""
    echo "Available examples:"
    echo "- examples/basic_usage.py - Simple usage example"
    echo "- examples/memory_optimized.py - Memory-efficient usage"
    echo ""
    echo "Configuration:"
    echo "- config/.env.example - Environment variables template"
    echo "- requirements.txt - Python dependencies"
    echo ""
    echo "For more advanced usage, see the full deployment guide:"
    echo "- DEEPSEEK_R1_LOCAL_DEPLOYMENT_GUIDE.md"
    echo ""
    echo "Troubleshooting:"
    echo "- Run: python -c 'import torch; print(torch.cuda.is_available())'"
    echo "- Check GPU: nvidia-smi"
    echo "- Memory issues: Use 4-bit quantization"
    echo ""
}

# Main installation flow
main() {
    echo "Starting DeepSeek R1-0528 installation..."
    echo ""
    
    # Check prerequisites
    if ! command_exists python3; then
        echo "❌ Python 3 not found. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Install system dependencies
    install_system_deps
    
    # Check NVIDIA setup
    check_nvidia
    
    # Setup Python environment
    setup_python_env
    
    # Install PyTorch
    install_pytorch
    
    # Install core dependencies
    install_core_deps
    
    # Install optional dependencies
    install_optional_deps
    
    # Test installation
    test_installation
    
    # Optional model download
    download_model
    
    # Print final instructions
    print_instructions
}

# Run main function
main "$@"