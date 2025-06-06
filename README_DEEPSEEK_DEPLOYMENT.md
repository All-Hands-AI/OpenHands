# DeepSeek R1-0528 Local Deployment

Complete implementation guide for setting up and using DeepSeek R1-0528 locally across different environments and deployment methods.

## 🚀 Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-repo/deepseek-deployment.git
cd deepseek-deployment

# Run the installation script
chmod +x setup_scripts/install_deepseek.sh
./setup_scripts/install_deepseek.sh

# Activate environment and test
source deepseek_env/bin/activate
python examples/basic_deepseek_usage.py
```

### Option 2: Manual Installation

```bash
# Create virtual environment
python3 -m venv deepseek_env
source deepseek_env/bin/activate

# Install dependencies
pip install -r requirements_deepseek.txt

# Install PyTorch with CUDA (if available)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Test installation
python examples/basic_deepseek_usage.py
```

### Option 3: Docker Deployment

```bash
# Build and run with Docker Compose
cd docker_examples
docker-compose -f docker-compose.deepseek.yml up -d

# Access services
# - Basic usage: docker logs deepseek-basic
# - API server: http://localhost:8000
# - Jupyter Lab: http://localhost:8888 (token: deepseek123)
# - Monitoring: http://localhost:3000 (admin/deepseek123)
```

## 📋 System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows 10/11
- **Python**: 3.8 or higher
- **RAM**: 16GB system memory
- **Storage**: 100GB free space
- **Internet**: For initial model download

### Recommended Requirements
- **RAM**: 32GB+ system memory
- **GPU**: NVIDIA GPU with 16GB+ VRAM
- **Storage**: 200GB+ NVMe SSD
- **CPU**: 8+ cores

### GPU Support
- **NVIDIA GPUs**: RTX 3090, RTX 4090, A100, H100, etc.
- **CUDA**: Version 11.8 or 12.x
- **Drivers**: Latest NVIDIA drivers

## 🛠️ Installation Methods

### 1. Transformers Library Integration

#### Pipeline Method (High-level)
```python
from transformers import pipeline

# Create pipeline with quantization
pipe = pipeline(
    "text-generation",
    model="deepseek-ai/DeepSeek-R1-0528",
    trust_remote_code=True,
    torch_dtype="float16",
    device_map="auto"
)

# Generate text
messages = [{"role": "user", "content": "Explain quantum computing"}]
response = pipe(messages, max_new_tokens=256)
```

#### Direct Model Loading (Low-level)
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load with 4-bit quantization
tokenizer = AutoTokenizer.from_pretrained(
    "deepseek-ai/DeepSeek-R1-0528",
    trust_remote_code=True
)

model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-R1-0528",
    trust_remote_code=True,
    torch_dtype=torch.float16,
    device_map="auto",
    load_in_4bit=True
)
```

### 2. vLLM Server Setup

```bash
# Install vLLM
pip install vllm

# Start server
vllm serve "deepseek-ai/DeepSeek-R1-0528" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.9

# Test API
curl -X POST "http://localhost:8000/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [{"role": "user", "content": "Hello!"}],
        "max_tokens": 100
    }'
```

### 3. Kaggle Notebook Setup

```python
# Install in Kaggle
!pip install transformers>=4.37.0 accelerate bitsandbytes

# Memory-optimized loading
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-R1-0528",
    trust_remote_code=True,
    quantization_config=quantization_config,
    device_map="auto",
    max_memory={"0": "14GB", "cpu": "12GB"}
)
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Model settings
export MODEL_NAME="deepseek-ai/DeepSeek-R1-0528"
export QUANTIZATION="4bit"
export MAX_MEMORY_GPU="20GB"
export MAX_MEMORY_CPU="30GB"

# Server settings
export HOST="0.0.0.0"
export PORT="8000"
export GPU_MEMORY_UTILIZATION="0.9"

# Cache settings
export HF_HOME="./cache/huggingface"
export TRANSFORMERS_CACHE="./cache/huggingface"
```

### Quantization Strategies

| Strategy | Memory Usage | Speed | Quality |
|----------|--------------|-------|---------|
| FP16 | ~50GB | Fastest | Best |
| 8-bit | ~25GB | Fast | Good |
| 4-bit | ~12GB | Moderate | Good |

```python
# 4-bit quantization (recommended for most users)
from transformers import BitsAndBytesConfig

config_4bit = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# 8-bit quantization
config_8bit = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0
)
```

## 📊 Performance Optimization

### Memory Optimization
```python
import torch
import gc

# Enable optimizations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.benchmark = True

# Memory cleanup
def cleanup_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
```

### Batch Processing
```python
# Process multiple prompts efficiently
prompts = [
    "Explain machine learning",
    "Write a Python function",
    "Describe quantum physics"
]

# Tokenize batch
inputs = tokenizer(
    prompts,
    return_tensors="pt",
    padding=True,
    truncation=True,
    max_length=2048
)

# Generate batch
outputs = model.generate(
    **inputs,
    max_new_tokens=256,
    temperature=0.7,
    do_sample=True
)
```

## 🐳 Docker Deployment

### Basic Container
```bash
# Build image
docker build -f docker_examples/Dockerfile.deepseek -t deepseek-r1 .

# Run container
docker run --gpus all -p 8000:8000 deepseek-r1
```

### Production Stack
```bash
# Start full stack
cd docker_examples
docker-compose -f docker-compose.deepseek.yml up -d

# Services available:
# - API Server: http://localhost:8000
# - Jupyter Lab: http://localhost:8888
# - Monitoring: http://localhost:3000
# - Prometheus: http://localhost:9090
```

## 🔍 Monitoring and Logging

### Health Checks
```python
# Check model health
def health_check():
    try:
        test_input = "Hello"
        inputs = tokenizer(test_input, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=10)
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Performance Metrics
```python
import time

def benchmark_generation(prompt, runs=5):
    times = []
    for _ in range(runs):
        start = time.time()
        # Generate text
        end = time.time()
        times.append(end - start)
    
    return {
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times)
    }
```

## 🚨 Troubleshooting

### Common Issues

#### CUDA Out of Memory
```bash
# Solutions:
# 1. Use 4-bit quantization
# 2. Reduce max_length
# 3. Clear CUDA cache
python -c "import torch; torch.cuda.empty_cache()"
```

#### Model Loading Errors
```bash
# Check internet connection
ping huggingface.co

# Verify model access
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-R1-0528', trust_remote_code=True)"

# Check disk space
df -h
```

#### Slow Inference
```python
# Enable optimizations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.benchmark = True

# Use Flash Attention (if available)
pip install flash-attn

# Consider vLLM for production
pip install vllm
```

### Diagnostic Script
```bash
# Run system diagnostics
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name()}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
```

## 📚 Examples

### Basic Usage
```python
# See examples/basic_deepseek_usage.py
python examples/basic_deepseek_usage.py
```

### Memory Optimized
```python
# See examples/memory_optimized_deepseek.py
python examples/memory_optimized_deepseek.py
```

### API Server
```python
# Start vLLM server
vllm serve "deepseek-ai/DeepSeek-R1-0528"

# Use with OpenAI client
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1-0528",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## 🔗 Additional Resources

- **Full Deployment Guide**: [DEEPSEEK_R1_LOCAL_DEPLOYMENT_GUIDE.md](DEEPSEEK_R1_LOCAL_DEPLOYMENT_GUIDE.md)
- **Model Card**: [DeepSeek R1-0528 on Hugging Face](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528)
- **vLLM Documentation**: [vLLM Docs](https://docs.vllm.ai/)
- **Transformers Documentation**: [Hugging Face Transformers](https://huggingface.co/docs/transformers/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

- DeepSeek R1-0528 is a large language model that requires significant computational resources
- GPU acceleration is highly recommended for practical use
- Model outputs should be reviewed and validated for production use
- Ensure compliance with DeepSeek's usage terms and conditions

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the full deployment guide
3. Search existing issues on GitHub
4. Create a new issue with detailed information about your setup and error

---

**Happy coding with DeepSeek R1-0528! 🚀**