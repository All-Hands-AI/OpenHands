# DeepSeek R1-0528 Local Deployment Guide

## Complete Implementation Guide for All Deployment Scenarios

This comprehensive guide covers setting up and using DeepSeek R1-0528 (deepseek-ai/DeepSeek-R1-0528) locally across different environments and deployment methods.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Transformers Library Integration](#transformers-library-integration)
3. [Kaggle Notebook Implementation](#kaggle-notebook-implementation)
4. [vLLM Local Server Setup](#vllm-local-server-setup)
5. [Docker Deployment](#docker-deployment)
6. [Production-Ready Features](#production-ready-features)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

## Hardware Requirements

### Minimum Requirements
- **RAM**: 32GB system RAM
- **VRAM**: 24GB GPU memory (for full precision)
- **Storage**: 100GB free space
- **CPU**: 8+ cores recommended

### Recommended Requirements
- **RAM**: 64GB+ system RAM
- **VRAM**: 48GB+ GPU memory (A100, H100)
- **Storage**: 200GB+ NVMe SSD
- **CPU**: 16+ cores, high clock speed

### Optimization Options
- **4-bit Quantization**: Reduces VRAM to ~8GB
- **8-bit Quantization**: Reduces VRAM to ~16GB
- **CPU-only Mode**: Requires 64GB+ RAM, slower inference

## 1. Transformers Library Integration

### Environment Setup

```bash
# Create virtual environment
python -m venv deepseek_env
source deepseek_env/bin/activate  # Linux/Mac
# deepseek_env\Scripts\activate  # Windows

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers>=4.37.0
pip install accelerate>=0.26.0
pip install bitsandbytes>=0.42.0
pip install flash-attn>=2.5.0
pip install sentencepiece
pip install protobuf
```

### A) Pipeline Method (High-level)

```python
import torch
from transformers import pipeline
import logging
import time
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekPipelineManager:
    """High-level pipeline manager for DeepSeek R1-0528"""
    
    def __init__(
        self,
        model_name: str = "deepseek-ai/DeepSeek-R1-0528",
        device: Optional[str] = None,
        quantization: Optional[str] = None,
        max_memory: Optional[Dict[str, str]] = None
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.quantization = quantization
        self.max_memory = max_memory
        self.pipe = None
        
    def setup_pipeline(self) -> None:
        """Initialize the pipeline with optimizations"""
        try:
            logger.info(f"Setting up pipeline for {self.model_name}")
            
            # Configure device map and quantization
            device_map = "auto" if self.device == "cuda" else None
            
            # Quantization configuration
            quantization_config = None
            if self.quantization == "4bit":
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif self.quantization == "8bit":
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            
            # Pipeline configuration
            pipeline_kwargs = {
                "model": self.model_name,
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "device_map": device_map,
            }
            
            if quantization_config:
                pipeline_kwargs["quantization_config"] = quantization_config
            
            if self.max_memory:
                pipeline_kwargs["max_memory"] = self.max_memory
            
            # Create pipeline
            self.pipe = pipeline(
                "text-generation",
                **pipeline_kwargs
            )
            
            logger.info("Pipeline setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup pipeline: {e}")
            raise
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate response from messages"""
        if not self.pipe:
            raise RuntimeError("Pipeline not initialized. Call setup_pipeline() first.")
        
        try:
            start_time = time.time()
            
            generation_kwargs = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": do_sample,
                "pad_token_id": self.pipe.tokenizer.eos_token_id,
                "return_full_text": False
            }
            
            if stream:
                return self._generate_streaming(messages, **generation_kwargs)
            else:
                result = self.pipe(messages, **generation_kwargs)
                
                end_time = time.time()
                
                return {
                    "response": result[0]["generated_text"],
                    "generation_time": end_time - start_time,
                    "model": self.model_name
                }
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _generate_streaming(self, messages: List[Dict[str, str]], **kwargs):
        """Generate streaming response"""
        # Note: Streaming requires custom implementation with model.generate()
        # This is a placeholder for the streaming interface
        logger.warning("Streaming not implemented in pipeline mode. Use direct model loading.")
        return self.pipe(messages, **kwargs)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics"""
        if not self.pipe:
            return {"status": "not_initialized"}
        
        model = self.pipe.model
        tokenizer = self.pipe.tokenizer
        
        # Calculate model size
        param_count = sum(p.numel() for p in model.parameters())
        param_size_mb = param_count * 4 / (1024 * 1024)  # Assuming float32
        
        return {
            "model_name": self.model_name,
            "device": str(model.device) if hasattr(model, 'device') else "unknown",
            "parameter_count": param_count,
            "model_size_mb": param_size_mb,
            "vocab_size": tokenizer.vocab_size,
            "max_position_embeddings": getattr(model.config, 'max_position_embeddings', 'unknown')
        }

# Usage Example
def main():
    """Example usage of DeepSeek Pipeline Manager"""
    
    # Initialize with 4-bit quantization for memory efficiency
    manager = DeepSeekPipelineManager(
        quantization="4bit",
        max_memory={"0": "20GB", "cpu": "30GB"}
    )
    
    # Setup pipeline
    manager.setup_pipeline()
    
    # Print model info
    info = manager.get_model_info()
    print(f"Model Info: {info}")
    
    # Example conversation
    messages = [
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ]
    
    # Generate response
    response = manager.generate_response(
        messages=messages,
        max_new_tokens=256,
        temperature=0.7
    )
    
    print(f"Response: {response['response']}")
    print(f"Generation time: {response['generation_time']:.2f}s")

if __name__ == "__main__":
    main()
```

### B) Direct Model Loading (Low-level)

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import logging
import time
from typing import List, Dict, Any, Optional, Iterator
import gc

logger = logging.getLogger(__name__)

class DeepSeekDirectModel:
    """Direct model loading with advanced features"""
    
    def __init__(
        self,
        model_name: str = "deepseek-ai/DeepSeek-R1-0528",
        device: Optional[str] = None,
        quantization: Optional[str] = None,
        max_memory: Optional[Dict[str, str]] = None,
        cache_dir: Optional[str] = None
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.quantization = quantization
        self.max_memory = max_memory
        self.cache_dir = cache_dir
        self.model = None
        self.tokenizer = None
        self.generation_config = None
        
    def load_model(self) -> None:
        """Load model and tokenizer with optimizations"""
        try:
            logger.info(f"Loading model {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=self.cache_dir
            )
            
            # Configure model loading parameters
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "cache_dir": self.cache_dir,
                "low_cpu_mem_usage": True,
            }
            
            # Device mapping
            if self.device == "cuda":
                model_kwargs["device_map"] = "auto"
                if self.max_memory:
                    model_kwargs["max_memory"] = self.max_memory
            
            # Quantization configuration
            if self.quantization == "4bit":
                from transformers import BitsAndBytesConfig
                model_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif self.quantization == "8bit":
                from transformers import BitsAndBytesConfig
                model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # Setup generation config
            self.generation_config = GenerationConfig(
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate response with advanced options"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Format messages for the model
            formatted_input = self._format_messages(messages)
            
            # Tokenize input
            inputs = self.tokenizer(
                formatted_input,
                return_tensors="pt",
                truncation=True,
                max_length=4096
            )
            
            if self.device == "cuda":
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Update generation config
            generation_config = GenerationConfig(
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            
            start_time = time.time()
            
            if stream:
                return self._generate_streaming(inputs, generation_config)
            else:
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        generation_config=generation_config,
                        return_dict_in_generate=True,
                        output_scores=True
                    )
                
                # Decode response
                response_tokens = outputs.sequences[0][inputs['input_ids'].shape[1]:]
                response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
                
                end_time = time.time()
                
                return {
                    "response": response,
                    "generation_time": end_time - start_time,
                    "input_tokens": inputs['input_ids'].shape[1],
                    "output_tokens": len(response_tokens),
                    "model": self.model_name
                }
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _generate_streaming(
        self,
        inputs: Dict[str, torch.Tensor],
        generation_config: GenerationConfig
    ) -> Iterator[Dict[str, Any]]:
        """Generate streaming response"""
        try:
            from transformers import TextIteratorStreamer
            import threading
            
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )
            
            generation_kwargs = {
                **inputs,
                "generation_config": generation_config,
                "streamer": streamer,
            }
            
            # Start generation in separate thread
            thread = threading.Thread(
                target=self.model.generate,
                kwargs=generation_kwargs
            )
            thread.start()
            
            # Yield tokens as they're generated
            generated_text = ""
            for new_text in streamer:
                generated_text += new_text
                yield {
                    "delta": new_text,
                    "accumulated": generated_text,
                    "finished": False
                }
            
            thread.join()
            
            yield {
                "delta": "",
                "accumulated": generated_text,
                "finished": True
            }
            
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for the model"""
        # DeepSeek R1 uses a specific chat format
        formatted = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                formatted += f"User: {content}\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n"
            elif role == "system":
                formatted += f"System: {content}\n"
        
        formatted += "Assistant: "
        return formatted
    
    def batch_generate(
        self,
        batch_messages: List[List[Dict[str, str]]],
        max_new_tokens: int = 512,
        temperature: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Generate responses for multiple conversations in batch"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Format all inputs
            formatted_inputs = [self._format_messages(msgs) for msgs in batch_messages]
            
            # Tokenize batch
            inputs = self.tokenizer(
                formatted_inputs,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=4096
            )
            
            if self.device == "cuda":
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate batch
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # Decode responses
            results = []
            for i, output in enumerate(outputs):
                response_tokens = output[inputs['input_ids'][i].shape[0]:]
                response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
                
                results.append({
                    "response": response,
                    "input_tokens": inputs['input_ids'][i].shape[0],
                    "output_tokens": len(response_tokens),
                    "batch_index": i
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Batch generation failed: {e}")
            raise
    
    def cleanup(self) -> None:
        """Clean up model and free memory"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        gc.collect()
        logger.info("Model cleanup completed")

# Usage Example
def main():
    """Example usage of DeepSeek Direct Model"""
    
    # Initialize model
    model = DeepSeekDirectModel(
        quantization="4bit",
        max_memory={"0": "20GB", "cpu": "30GB"}
    )
    
    # Load model
    model.load_model()
    
    # Single generation
    messages = [
        {"role": "user", "content": "Write a Python function to calculate fibonacci numbers."}
    ]
    
    response = model.generate_response(messages, max_new_tokens=256)
    print(f"Response: {response['response']}")
    
    # Streaming generation
    print("\nStreaming response:")
    for chunk in model._generate_streaming(
        model.tokenizer(
            model._format_messages(messages),
            return_tensors="pt"
        ),
        model.generation_config
    ):
        if chunk["delta"]:
            print(chunk["delta"], end="", flush=True)
        if chunk["finished"]:
            print("\n[Generation finished]")
            break
    
    # Batch generation
    batch_messages = [
        [{"role": "user", "content": "What is machine learning?"}],
        [{"role": "user", "content": "Explain neural networks."}]
    ]
    
    batch_results = model.batch_generate(batch_messages, max_new_tokens=128)
    for i, result in enumerate(batch_results):
        print(f"Batch {i}: {result['response'][:100]}...")
    
    # Cleanup
    model.cleanup()

if __name__ == "__main__":
    main()
```

## 2. Kaggle Notebook Implementation

### Kaggle Environment Setup

```python
# Cell 1: Environment Setup and Installation
import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_requirements():
    """Install required packages in Kaggle environment"""
    requirements = [
        "transformers>=4.37.0",
        "accelerate>=0.26.0",
        "bitsandbytes>=0.42.0",
        "sentencepiece",
        "protobuf",
        "torch",
        "torchvision",
        "torchaudio"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logger.info(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {package}: {e}")

# Install packages
install_requirements()

# Check GPU availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name()}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

```python
# Cell 2: Memory Optimization for Kaggle
import gc
import psutil
import torch
from typing import Dict, Any

class KaggleMemoryManager:
    """Memory management utilities for Kaggle environment"""
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get current memory usage information"""
        # System memory
        memory = psutil.virtual_memory()
        
        info = {
            "system_memory_total_gb": memory.total / 1e9,
            "system_memory_used_gb": memory.used / 1e9,
            "system_memory_available_gb": memory.available / 1e9,
            "system_memory_percent": memory.percent
        }
        
        # GPU memory if available
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory
            gpu_allocated = torch.cuda.memory_allocated()
            gpu_reserved = torch.cuda.memory_reserved()
            
            info.update({
                "gpu_memory_total_gb": gpu_memory / 1e9,
                "gpu_memory_allocated_gb": gpu_allocated / 1e9,
                "gpu_memory_reserved_gb": gpu_reserved / 1e9,
                "gpu_memory_free_gb": (gpu_memory - gpu_reserved) / 1e9
            })
        
        return info
    
    @staticmethod
    def cleanup_memory():
        """Aggressive memory cleanup"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    @staticmethod
    def optimize_for_kaggle() -> Dict[str, str]:
        """Get optimal settings for Kaggle environment"""
        memory_info = KaggleMemoryManager.get_memory_info()
        
        # Determine optimal configuration based on available memory
        if memory_info.get("gpu_memory_total_gb", 0) >= 15:
            return {
                "quantization": "8bit",
                "max_memory": {"0": "14GB", "cpu": "12GB"},
                "batch_size": 2
            }
        elif memory_info.get("gpu_memory_total_gb", 0) >= 8:
            return {
                "quantization": "4bit",
                "max_memory": {"0": "7GB", "cpu": "8GB"},
                "batch_size": 1
            }
        else:
            return {
                "quantization": "4bit",
                "max_memory": {"cpu": "12GB"},
                "batch_size": 1
            }

# Check memory and get optimal settings
memory_manager = KaggleMemoryManager()
memory_info = memory_manager.get_memory_info()
optimal_config = memory_manager.optimize_for_kaggle()

print("Memory Information:")
for key, value in memory_info.items():
    print(f"  {key}: {value}")

print(f"\nOptimal Configuration for this environment:")
for key, value in optimal_config.items():
    print(f"  {key}: {value}")
```

```python
# Cell 3: DeepSeek Model Setup for Kaggle
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import time
from typing import List, Dict, Any

class KaggleDeepSeekModel:
    """DeepSeek model optimized for Kaggle environment"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.memory_manager = KaggleMemoryManager()
        
    def load_model(self):
        """Load model with Kaggle-optimized settings"""
        try:
            print("Loading DeepSeek R1-0528 model...")
            start_time = time.time()
            
            # Clean memory before loading
            self.memory_manager.cleanup_memory()
            
            # Load tokenizer
            print("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                "deepseek-ai/DeepSeek-R1-0528",
                trust_remote_code=True
            )
            
            # Configure quantization
            quantization_config = None
            if self.config["quantization"] == "4bit":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif self.config["quantization"] == "8bit":
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            
            # Load model
            print(f"Loading model with {self.config['quantization']} quantization...")
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16,
                "low_cpu_mem_usage": True,
                "device_map": "auto",
                "max_memory": self.config["max_memory"]
            }
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
            
            self.model = AutoModelForCausalLM.from_pretrained(
                "deepseek-ai/DeepSeek-R1-0528",
                **model_kwargs
            )
            
            load_time = time.time() - start_time
            print(f"Model loaded successfully in {load_time:.2f} seconds")
            
            # Print memory usage after loading
            memory_info = self.memory_manager.get_memory_info()
            print(f"Memory usage after loading:")
            print(f"  GPU allocated: {memory_info.get('gpu_memory_allocated_gb', 0):.2f} GB")
            print(f"  System memory used: {memory_info['system_memory_used_gb']:.2f} GB")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def generate_text(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """Generate text with memory monitoring"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")
        
        try:
            # Monitor memory before generation
            memory_before = self.memory_manager.get_memory_info()
            
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate
            start_time = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            generation_time = time.time() - start_time
            
            # Decode response
            response_tokens = outputs[0][inputs['input_ids'].shape[1]:]
            response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
            # Monitor memory after generation
            memory_after = self.memory_manager.get_memory_info()
            
            return {
                "response": response,
                "generation_time": generation_time,
                "input_tokens": inputs['input_ids'].shape[1],
                "output_tokens": len(response_tokens),
                "memory_before_gb": memory_before.get('gpu_memory_allocated_gb', 0),
                "memory_after_gb": memory_after.get('gpu_memory_allocated_gb', 0)
            }
            
        except Exception as e:
            print(f"Generation error: {e}")
            # Cleanup on error
            self.memory_manager.cleanup_memory()
            raise

# Initialize and load model
kaggle_model = KaggleDeepSeekModel(optimal_config)
kaggle_model.load_model()
```

```python
# Cell 4: Interactive Testing and Examples
def test_model_capabilities():
    """Test various model capabilities"""
    
    test_prompts = [
        {
            "name": "Code Generation",
            "prompt": "Write a Python function to implement binary search:",
            "max_tokens": 200
        },
        {
            "name": "Explanation",
            "prompt": "Explain the concept of machine learning in simple terms:",
            "max_tokens": 150
        },
        {
            "name": "Problem Solving",
            "prompt": "How would you optimize a slow database query?",
            "max_tokens": 180
        }
    ]
    
    results = []
    
    for test in test_prompts:
        print(f"\n{'='*50}")
        print(f"Test: {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print(f"{'='*50}")
        
        try:
            result = kaggle_model.generate_text(
                prompt=test['prompt'],
                max_new_tokens=test['max_tokens'],
                temperature=0.7
            )
            
            print(f"Response: {result['response']}")
            print(f"Generation time: {result['generation_time']:.2f}s")
            print(f"Tokens - Input: {result['input_tokens']}, Output: {result['output_tokens']}")
            print(f"Memory usage: {result['memory_after_gb']:.2f} GB")
            
            results.append({
                "test_name": test['name'],
                "success": True,
                "generation_time": result['generation_time'],
                "memory_usage": result['memory_after_gb']
            })
            
        except Exception as e:
            print(f"Error: {e}")
            results.append({
                "test_name": test['name'],
                "success": False,
                "error": str(e)
            })
        
        # Cleanup between tests
        kaggle_model.memory_manager.cleanup_memory()
        time.sleep(1)
    
    return results

# Run tests
test_results = test_model_capabilities()

# Summary
print(f"\n{'='*50}")
print("TEST SUMMARY")
print(f"{'='*50}")
successful_tests = [r for r in test_results if r['success']]
print(f"Successful tests: {len(successful_tests)}/{len(test_results)}")

if successful_tests:
    avg_time = sum(r['generation_time'] for r in successful_tests) / len(successful_tests)
    avg_memory = sum(r['memory_usage'] for r in successful_tests) / len(successful_tests)
    print(f"Average generation time: {avg_time:.2f}s")
    print(f"Average memory usage: {avg_memory:.2f} GB")
```

```python
# Cell 5: Kaggle-Specific Utilities and Data Handling
import json
import pandas as pd
from pathlib import Path

class KaggleDataHandler:
    """Handle data input/output in Kaggle environment"""
    
    def __init__(self, model: KaggleDeepSeekModel):
        self.model = model
        self.results_dir = Path("/kaggle/working/deepseek_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def process_csv_prompts(self, csv_path: str, prompt_column: str) -> pd.DataFrame:
        """Process prompts from CSV file"""
        try:
            # Load data
            df = pd.read_csv(csv_path)
            
            if prompt_column not in df.columns:
                raise ValueError(f"Column '{prompt_column}' not found in CSV")
            
            results = []
            
            for idx, row in df.iterrows():
                prompt = row[prompt_column]
                
                try:
                    print(f"Processing row {idx + 1}/{len(df)}: {prompt[:50]}...")
                    
                    result = self.model.generate_text(
                        prompt=prompt,
                        max_new_tokens=256,
                        temperature=0.7
                    )
                    
                    results.append({
                        "index": idx,
                        "prompt": prompt,
                        "response": result["response"],
                        "generation_time": result["generation_time"],
                        "input_tokens": result["input_tokens"],
                        "output_tokens": result["output_tokens"],
                        "success": True
                    })
                    
                except Exception as e:
                    print(f"Error processing row {idx}: {e}")
                    results.append({
                        "index": idx,
                        "prompt": prompt,
                        "response": "",
                        "generation_time": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "success": False,
                        "error": str(e)
                    })
                
                # Cleanup between generations
                self.model.memory_manager.cleanup_memory()
            
            # Create results DataFrame
            results_df = pd.DataFrame(results)
            
            # Save results
            output_path = self.results_dir / f"batch_results_{int(time.time())}.csv"
            results_df.to_csv(output_path, index=False)
            print(f"Results saved to: {output_path}")
            
            return results_df
            
        except Exception as e:
            print(f"Error processing CSV: {e}")
            raise
    
    def save_conversation(self, conversation: List[Dict[str, str]], filename: str):
        """Save conversation to JSON file"""
        output_path = self.results_dir / f"{filename}.json"
        with open(output_path, 'w') as f:
            json.dump(conversation, f, indent=2)
        print(f"Conversation saved to: {output_path}")
    
    def create_sample_dataset(self) -> pd.DataFrame:
        """Create sample dataset for testing"""
        sample_prompts = [
            "Explain the difference between supervised and unsupervised learning",
            "Write a Python function to reverse a string",
            "What are the benefits of using Docker containers?",
            "How does gradient descent work in neural networks?",
            "Describe the SOLID principles in software engineering"
        ]
        
        df = pd.DataFrame({"prompts": sample_prompts})
        sample_path = self.results_dir / "sample_prompts.csv"
        df.to_csv(sample_path, index=False)
        print(f"Sample dataset created: {sample_path}")
        
        return df

# Initialize data handler
data_handler = KaggleDataHandler(kaggle_model)

# Create and process sample dataset
sample_df = data_handler.create_sample_dataset()
results_df = data_handler.process_csv_prompts(
    str(data_handler.results_dir / "sample_prompts.csv"),
    "prompts"
)

# Display results summary
print("\nBatch Processing Results:")
print(f"Total prompts: {len(results_df)}")
print(f"Successful: {results_df['success'].sum()}")
print(f"Failed: {(~results_df['success']).sum()}")
print(f"Average generation time: {results_df[results_df['success']]['generation_time'].mean():.2f}s")
```

```python
# Cell 6: Performance Monitoring and Optimization
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

class KagglePerformanceMonitor:
    """Monitor and visualize model performance in Kaggle"""
    
    def __init__(self):
        self.metrics = []
    
    def record_generation(self, result: Dict[str, Any], prompt_length: int):
        """Record generation metrics"""
        self.metrics.append({
            "timestamp": time.time(),
            "prompt_length": prompt_length,
            "generation_time": result.get("generation_time", 0),
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "memory_usage": result.get("memory_after_gb", 0),
            "tokens_per_second": result.get("output_tokens", 0) / max(result.get("generation_time", 1), 0.001)
        })
    
    def plot_performance_metrics(self):
        """Create performance visualization"""
        if not self.metrics:
            print("No metrics recorded yet")
            return
        
        df = pd.DataFrame(self.metrics)
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle("DeepSeek R1-0528 Performance Metrics", fontsize=16)
        
        # Generation time vs input length
        axes[0, 0].scatter(df["input_tokens"], df["generation_time"], alpha=0.7)
        axes[0, 0].set_xlabel("Input Tokens")
        axes[0, 0].set_ylabel("Generation Time (s)")
        axes[0, 0].set_title("Generation Time vs Input Length")
        
        # Tokens per second
        axes[0, 1].hist(df["tokens_per_second"], bins=20, alpha=0.7, edgecolor='black')
        axes[0, 1].set_xlabel("Tokens per Second")
        axes[0, 1].set_ylabel("Frequency")
        axes[0, 1].set_title("Generation Speed Distribution")
        
        # Memory usage over time
        axes[1, 0].plot(range(len(df)), df["memory_usage"], marker='o', alpha=0.7)
        axes[1, 0].set_xlabel("Generation Number")
        axes[1, 0].set_ylabel("Memory Usage (GB)")
        axes[1, 0].set_title("Memory Usage Over Time")
        
        # Output tokens vs generation time
        axes[1, 1].scatter(df["output_tokens"], df["generation_time"], alpha=0.7)
        axes[1, 1].set_xlabel("Output Tokens")
        axes[1, 1].set_ylabel("Generation Time (s)")
        axes[1, 1].set_title("Generation Time vs Output Length")
        
        plt.tight_layout()
        plt.savefig("/kaggle/working/deepseek_performance.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        # Print summary statistics
        print("\nPerformance Summary:")
        print(f"Average generation time: {df['generation_time'].mean():.2f}s")
        print(f"Average tokens per second: {df['tokens_per_second'].mean():.2f}")
        print(f"Average memory usage: {df['memory_usage'].mean():.2f} GB")
        print(f"Total generations: {len(df)}")

# Initialize performance monitor
perf_monitor = KagglePerformanceMonitor()

# Record metrics from previous results
for _, row in results_df.iterrows():
    if row['success']:
        perf_monitor.record_generation({
            "generation_time": row['generation_time'],
            "input_tokens": row['input_tokens'],
            "output_tokens": row['output_tokens'],
            "memory_after_gb": 8.0  # Estimated
        }, len(row['prompt']))

# Generate performance plots
perf_monitor.plot_performance_metrics()
```

## 3. vLLM Local Server Setup

### Installation and Basic Setup

```bash
#!/bin/bash
# setup_vllm_server.sh

# Create virtual environment
python -m venv vllm_env
source vllm_env/bin/activate

# Install vLLM with CUDA support
pip install vllm[cuda]

# Alternative: Install from source for latest features
# git clone https://github.com/vllm-project/vllm.git
# cd vllm
# pip install -e .

# Install additional dependencies
pip install fastapi uvicorn
pip install prometheus-client  # For metrics
pip install aiofiles  # For async file operations

echo "vLLM installation completed"
```

### Production-Ready vLLM Server

```python
# vllm_server.py
import asyncio
import logging
import time
import json
import os
from typing import Dict, List, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.utils import random_uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Request/Response Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="deepseek-ai/DeepSeek-R1-0528")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    max_tokens: Optional[int] = Field(default=512, ge=1, le=4096)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
    stream: Optional[bool] = Field(default=False)
    stop: Optional[List[str]] = Field(default=None)

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ServerConfig:
    """Server configuration"""
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-R1-0528")
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.max_model_len = int(os.getenv("MAX_MODEL_LEN", "4096"))
        self.gpu_memory_utilization = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.9"))
        self.tensor_parallel_size = int(os.getenv("TENSOR_PARALLEL_SIZE", "1"))
        self.quantization = os.getenv("QUANTIZATION", None)  # "awq", "gptq", etc.
        self.max_num_seqs = int(os.getenv("MAX_NUM_SEQS", "256"))
        self.max_num_batched_tokens = int(os.getenv("MAX_NUM_BATCHED_TOKENS", "8192"))

class DeepSeekVLLMServer:
    """Production-ready vLLM server for DeepSeek R1-0528"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.engine: Optional[AsyncLLMEngine] = None
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_generated": 0,
            "average_generation_time": 0.0
        }
    
    async def initialize_engine(self):
        """Initialize the vLLM async engine"""
        try:
            logger.info(f"Initializing vLLM engine for {self.config.model_name}")
            
            # Configure engine arguments
            engine_args = AsyncEngineArgs(
                model=self.config.model_name,
                tensor_parallel_size=self.config.tensor_parallel_size,
                gpu_memory_utilization=self.config.gpu_memory_utilization,
                max_model_len=self.config.max_model_len,
                max_num_seqs=self.config.max_num_seqs,
                max_num_batched_tokens=self.config.max_num_batched_tokens,
                quantization=self.config.quantization,
                trust_remote_code=True,
                enforce_eager=False,  # Use CUDA graphs for better performance
                disable_log_stats=False,
            )
            
            # Create async engine
            self.engine = AsyncLLMEngine.from_engine_args(engine_args)
            
            logger.info("vLLM engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vLLM engine: {e}")
            raise
    
    def format_messages(self, messages: List[ChatMessage]) -> str:
        """Format chat messages for the model"""
        formatted = ""
        for message in messages:
            role = message.role
            content = message.content
            
            if role == "user":
                formatted += f"User: {content}\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n"
            elif role == "system":
                formatted += f"System: {content}\n"
        
        formatted += "Assistant: "
        return formatted
    
    async def generate_completion(
        self,
        request: ChatCompletionRequest,
        request_id: str
    ) -> ChatCompletionResponse:
        """Generate non-streaming completion"""
        if not self.engine:
            raise HTTPException(status_code=503, detail="Engine not initialized")
        
        try:
            start_time = time.time()
            
            # Format prompt
            prompt = self.format_messages(request.messages)
            
            # Configure sampling parameters
            sampling_params = SamplingParams(
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
                stop=request.stop,
            )
            
            # Generate
            results = []
            async for request_output in self.engine.generate(
                prompt, sampling_params, request_id
            ):
                results.append(request_output)
            
            # Get final result
            final_output = results[-1]
            generated_text = final_output.outputs[0].text
            
            generation_time = time.time() - start_time
            
            # Update stats
            self.request_stats["total_requests"] += 1
            self.request_stats["successful_requests"] += 1
            self.request_stats["total_tokens_generated"] += len(final_output.outputs[0].token_ids)
            
            # Create response
            response = ChatCompletionResponse(
                id=request_id,
                created=int(time.time()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": len(final_output.prompt_token_ids),
                    "completion_tokens": len(final_output.outputs[0].token_ids),
                    "total_tokens": len(final_output.prompt_token_ids) + len(final_output.outputs[0].token_ids)
                }
            )
            
            logger.info(f"Generated completion in {generation_time:.2f}s")
            return response
            
        except Exception as e:
            self.request_stats["failed_requests"] += 1
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def generate_streaming_completion(
        self,
        request: ChatCompletionRequest,
        request_id: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion"""
        if not self.engine:
            raise HTTPException(status_code=503, detail="Engine not initialized")
        
        try:
            # Format prompt
            prompt = self.format_messages(request.messages)
            
            # Configure sampling parameters
            sampling_params = SamplingParams(
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
                stop=request.stop,
            )
            
            # Generate streaming
            previous_text = ""
            async for request_output in self.engine.generate(
                prompt, sampling_params, request_id
            ):
                current_text = request_output.outputs[0].text
                delta = current_text[len(previous_text):]
                
                if delta:
                    chunk = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": delta},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    previous_text = current_text
            
            # Send final chunk
            final_chunk = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            
            # Update stats
            self.request_stats["total_requests"] += 1
            self.request_stats["successful_requests"] += 1
            
        except Exception as e:
            self.request_stats["failed_requests"] += 1
            logger.error(f"Streaming generation failed: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "generation_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

# Global server instance
config = ServerConfig()
server = DeepSeekVLLMServer(config)

# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting DeepSeek vLLM server...")
    await server.initialize_engine()
    logger.info("Server startup completed")
    yield
    # Shutdown
    logger.info("Shutting down server...")

app = FastAPI(
    title="DeepSeek R1-0528 vLLM Server",
    description="Production-ready vLLM server for DeepSeek R1-0528",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    request_id = random_uuid()
    
    if request.stream:
        return StreamingResponse(
            server.generate_streaming_completion(request, request_id),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    else:
        return await server.generate_completion(request, request_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if server.engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    return {
        "status": "healthy",
        "model": config.model_name,
        "timestamp": int(time.time())
    }

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    return {
        "server_stats": server.request_stats,
        "model": config.model_name,
        "config": {
            "max_model_len": config.max_model_len,
            "tensor_parallel_size": config.tensor_parallel_size,
            "gpu_memory_utilization": config.gpu_memory_utilization
        }
    }

@app.get("/models")
async def list_models():
    """List available models (OpenAI-compatible)"""
    return {
        "object": "list",
        "data": [{
            "id": config.model_name,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "deepseek"
        }]
    }

if __name__ == "__main__":
    uvicorn.run(
        "vllm_server:app",
        host=config.host,
        port=config.port,
        workers=1,
        log_level="info",
        access_log=True
    )
```

### vLLM Server Management Scripts

```bash
#!/bin/bash
# start_vllm_server.sh

# Configuration
MODEL_NAME="deepseek-ai/DeepSeek-R1-0528"
HOST="0.0.0.0"
PORT="8000"
GPU_MEMORY_UTILIZATION="0.9"
TENSOR_PARALLEL_SIZE="1"
MAX_MODEL_LEN="4096"

# Export environment variables
export MODEL_NAME=$MODEL_NAME
export HOST=$HOST
export PORT=$PORT
export GPU_MEMORY_UTILIZATION=$GPU_MEMORY_UTILIZATION
export TENSOR_PARALLEL_SIZE=$TENSOR_PARALLEL_SIZE
export MAX_MODEL_LEN=$MAX_MODEL_LEN

# Start server
echo "Starting DeepSeek vLLM server..."
echo "Model: $MODEL_NAME"
echo "Host: $HOST:$PORT"
echo "GPU Memory Utilization: $GPU_MEMORY_UTILIZATION"

python vllm_server.py
```

```bash
#!/bin/bash
# test_vllm_server.sh

SERVER_URL="http://localhost:8000"

echo "Testing vLLM server at $SERVER_URL"

# Test health endpoint
echo "1. Health check:"
curl -s "$SERVER_URL/health" | jq .

echo -e "\n2. List models:"
curl -s "$SERVER_URL/models" | jq .

echo -e "\n3. Chat completion (non-streaming):"
curl -s -X POST "$SERVER_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [
            {
                "role": "user",
                "content": "Write a Python function to calculate factorial."
            }
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }' | jq .

echo -e "\n4. Chat completion (streaming):"
curl -s -X POST "$SERVER_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [
            {
                "role": "user",
                "content": "Explain machine learning briefly."
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "stream": true
    }'

echo -e "\n5. Server stats:"
curl -s "$SERVER_URL/stats" | jq .
```

### vLLM Client Library

```python
# vllm_client.py
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class DeepSeekVLLMClient:
    """Async client for DeepSeek vLLM server"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 300,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models"""
        async with self.session.get(f"{self.base_url}/models") as response:
            return await response.json()
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-ai/DeepSeek-R1-0528",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion"""
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            **kwargs
        }
        
        if stream:
            return await self._stream_completion(payload)
        else:
            return await self._single_completion(payload)
    
    async def _single_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate single completion"""
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _stream_completion(self, payload: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming completion"""
        async with self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_text
                )
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        yield chunk
                    except json.JSONDecodeError:
                        continue

# Usage examples
async def example_usage():
    """Example usage of the vLLM client"""
    
    async with DeepSeekVLLMClient() as client:
        # Health check
        health = await client.health_check()
        print(f"Server health: {health}")
        
        # Single completion
        messages = [
            {"role": "user", "content": "Write a Python function to sort a list."}
        ]
        
        response = await client.chat_completion(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        print(f"Response: {response['choices'][0]['message']['content']}")
        
        # Streaming completion
        print("\nStreaming response:")
        async for chunk in client.chat_completion(
            messages=[{"role": "user", "content": "Explain recursion."}],
            max_tokens=150,
            stream=True
        ):
            if 'choices' in chunk and chunk['choices']:
                delta = chunk['choices'][0].get('delta', {})
                if 'content' in delta:
                    print(delta['content'], end='', flush=True)
        
        print("\n[Streaming completed]")

if __name__ == "__main__":
    asyncio.run(example_usage())
```

## 4. Docker Deployment

### Dockerfile for vLLM Server

```dockerfile
# Dockerfile.vllm
FROM nvidia/cuda:11.8-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install vLLM
RUN pip3 install vllm[cuda]

# Copy application code
COPY vllm_server.py .
COPY start_server.sh .
RUN chmod +x start_server.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start server
CMD ["./start_server.sh"]
```

```dockerfile
# Dockerfile.transformers
FROM nvidia/cuda:11.8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip3 install transformers>=4.37.0 accelerate>=0.26.0 bitsandbytes>=0.42.0
RUN pip3 install fastapi uvicorn aiofiles

# Copy application code
COPY transformers_server.py .
COPY requirements.txt .

EXPOSE 8000

CMD ["python3", "transformers_server.py"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  deepseek-vllm:
    build:
      context: .
      dockerfile: Dockerfile.vllm
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=deepseek-ai/DeepSeek-R1-0528
      - GPU_MEMORY_UTILIZATION=0.9
      - TENSOR_PARALLEL_SIZE=1
      - MAX_MODEL_LEN=4096
      - HOST=0.0.0.0
      - PORT=8000
    volumes:
      - model_cache:/root/.cache/huggingface
      - ./logs:/app/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  deepseek-transformers:
    build:
      context: .
      dockerfile: Dockerfile.transformers
    ports:
      - "8001:8000"
    environment:
      - MODEL_NAME=deepseek-ai/DeepSeek-R1-0528
      - QUANTIZATION=4bit
      - MAX_MEMORY_GPU=20GB
      - MAX_MEMORY_CPU=30GB
    volumes:
      - model_cache:/root/.cache/huggingface
      - ./logs:/app/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - deepseek-vllm
      - deepseek-transformers
    restart: unless-stopped

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  model_cache:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

### Nginx Load Balancer Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream deepseek_backend {
        least_conn;
        server deepseek-vllm:8000 weight=3 max_fails=3 fail_timeout=30s;
        server deepseek-transformers:8000 weight=1 max_fails=3 fail_timeout=30s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=chat:10m rate=5r/s;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'rt=$request_time uct="$upstream_connect_time" '
                   'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain application/json application/javascript text/css;

    server {
        listen 80;
        server_name localhost;

        # Health check endpoint
        location /health {
            access_log off;
            proxy_pass http://deepseek_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }

        # Chat completions with rate limiting
        location /v1/chat/completions {
            limit_req zone=chat burst=10 nodelay;
            
            proxy_pass http://deepseek_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts for long-running requests
            proxy_connect_timeout 30s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            
            # Buffering settings for streaming
            proxy_buffering off;
            proxy_cache off;
            
            # Headers for streaming
            proxy_set_header Connection '';
            proxy_http_version 1.1;
            chunked_transfer_encoding off;
        }

        # Other API endpoints
        location /v1/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://deepseek_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout 10s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Metrics endpoint (restricted access)
        location /stats {
            allow 127.0.0.1;
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 192.168.0.0/16;
            deny all;
            
            proxy_pass http://deepseek_backend;
            proxy_set_header Host $host;
        }
    }
}
```

### Production Deployment Scripts

```bash
#!/bin/bash
# deploy.sh

set -e

echo "Deploying DeepSeek R1-0528 Production Environment"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Check NVIDIA Docker runtime
if ! docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi >/dev/null 2>&1; then
    echo "NVIDIA Docker runtime not available. GPU acceleration will not work."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
mkdir -p logs ssl grafana/dashboards grafana/datasources

# Generate SSL certificates (self-signed for development)
if [ ! -f ssl/server.crt ]; then
    echo "Generating SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/server.key \
        -out ssl/server.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Create Prometheus configuration
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'deepseek-vllm'
    static_configs:
      - targets: ['deepseek-vllm:8000']
    metrics_path: '/stats'
    scrape_interval: 30s

  - job_name: 'deepseek-transformers'
    static_configs:
      - targets: ['deepseek-transformers:8000']
    metrics_path: '/stats'
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/nginx_status'
    scrape_interval: 15s
EOF

# Create Grafana datasource configuration
mkdir -p grafana/datasources
cat > grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Health checks
echo "Performing health checks..."

# Check vLLM server
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✓ vLLM server is healthy"
else
    echo "✗ vLLM server health check failed"
fi

# Check Transformers server
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✓ Transformers server is healthy"
else
    echo "✗ Transformers server health check failed"
fi

# Check Nginx
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo "✓ Nginx load balancer is healthy"
else
    echo "✗ Nginx health check failed"
fi

echo "Deployment completed!"
echo ""
echo "Services available at:"
echo "  - Main API (load balanced): http://localhost"
echo "  - vLLM Server: http://localhost:8000"
echo "  - Transformers Server: http://localhost:8001"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "To view logs: docker-compose logs -f [service_name]"
echo "To stop services: docker-compose down"
```

```bash
#!/bin/bash
# monitor.sh

echo "DeepSeek R1-0528 Service Monitor"
echo "================================"

while true; do
    clear
    echo "Service Status - $(date)"
    echo "========================"
    
    # Check Docker containers
    echo "Docker Containers:"
    docker-compose ps
    echo ""
    
    # Check API endpoints
    echo "API Health Checks:"
    
    # vLLM server
    if curl -s -f http://localhost:8000/health >/dev/null; then
        echo "✓ vLLM Server: HEALTHY"
    else
        echo "✗ vLLM Server: UNHEALTHY"
    fi
    
    # Transformers server
    if curl -s -f http://localhost:8001/health >/dev/null; then
        echo "✓ Transformers Server: HEALTHY"
    else
        echo "✗ Transformers Server: UNHEALTHY"
    fi
    
    # Load balancer
    if curl -s -f http://localhost/health >/dev/null; then
        echo "✓ Load Balancer: HEALTHY"
    else
        echo "✗ Load Balancer: UNHEALTHY"
    fi
    
    echo ""
    
    # Get stats from vLLM server
    echo "vLLM Server Stats:"
    curl -s http://localhost:8000/stats | jq '.server_stats' 2>/dev/null || echo "Stats unavailable"
    
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 10
done
```

## 5. Performance Optimization

### GPU Acceleration Setup

```python
# gpu_optimization.py
import torch
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GPUOptimizer:
    """GPU optimization utilities for DeepSeek R1-0528"""
    
    @staticmethod
    def detect_gpu_config() -> Dict[str, Any]:
        """Detect optimal GPU configuration"""
        config = {
            "cuda_available": torch.cuda.is_available(),
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "devices": []
        }
        
        if config["cuda_available"]:
            for i in range(config["gpu_count"]):
                props = torch.cuda.get_device_properties(i)
                device_info = {
                    "device_id": i,
                    "name": props.name,
                    "total_memory_gb": props.total_memory / 1e9,
                    "major": props.major,
                    "minor": props.minor,
                    "multi_processor_count": props.multi_processor_count
                }
                config["devices"].append(device_info)
        
        return config
    
    @staticmethod
    def optimize_cuda_settings():
        """Apply optimal CUDA settings"""
        if not torch.cuda.is_available():
            logger.warning("CUDA not available, skipping GPU optimizations")
            return
        
        # Enable TensorFloat-32 (TF32) for better performance on Ampere GPUs
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        # Enable cuDNN benchmark for consistent input sizes
        torch.backends.cudnn.benchmark = True
        
        # Set memory fraction to avoid OOM
        torch.cuda.set_per_process_memory_fraction(0.95)
        
        # Enable memory pool for faster allocation
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
        
        logger.info("CUDA optimizations applied")
    
    @staticmethod
    def get_optimal_device_map(model_size_gb: float, available_gpus: int) -> Dict[str, str]:
        """Calculate optimal device mapping for model sharding"""
        if available_gpus == 0:
            return {"": "cpu"}
        
        if available_gpus == 1:
            return {"": "cuda:0"}
        
        # Multi-GPU sharding strategy
        device_map = {}
        
        # Distribute layers across GPUs
        if model_size_gb > 20:  # Large model requiring sharding
            # Example sharding for DeepSeek R1-0528
            layers_per_gpu = 32 // available_gpus
            
            for gpu_id in range(available_gpus):
                start_layer = gpu_id * layers_per_gpu
                end_layer = min((gpu_id + 1) * layers_per_gpu, 32)
                
                for layer in range(start_layer, end_layer):
                    device_map[f"model.layers.{layer}"] = f"cuda:{gpu_id}"
            
            # Place embedding and output layers
            device_map["model.embed_tokens"] = "cuda:0"
            device_map["model.norm"] = f"cuda:{available_gpus-1}"
            device_map["lm_head"] = f"cuda:{available_gpus-1}"
        else:
            # Single GPU for smaller models
            device_map = {"": "cuda:0"}
        
        return device_map

# Usage example
gpu_config = GPUOptimizer.detect_gpu_config()
print(f"GPU Configuration: {gpu_config}")

GPUOptimizer.optimize_cuda_settings()
device_map = GPUOptimizer.get_optimal_device_map(model_size_gb=25, available_gpus=gpu_config["gpu_count"])
print(f"Optimal device map: {device_map}")
```

### Quantization Strategies

```python
# quantization_utils.py
import torch
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class QuantizationManager:
    """Advanced quantization strategies for DeepSeek R1-0528"""
    
    @staticmethod
    def get_4bit_config(
        compute_dtype: torch.dtype = torch.float16,
        quant_type: str = "nf4",
        use_double_quant: bool = True
    ) -> BitsAndBytesConfig:
        """Get optimized 4-bit quantization config"""
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=use_double_quant,
            bnb_4bit_quant_type=quant_type,  # "fp4" or "nf4"
            bnb_4bit_quant_storage=torch.uint8
        )
    
    @staticmethod
    def get_8bit_config() -> BitsAndBytesConfig:
        """Get optimized 8-bit quantization config"""
        return BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
            llm_int8_enable_fp32_cpu_offload=True
        )
    
    @staticmethod
    def benchmark_quantization_methods(
        model_name: str = "deepseek-ai/DeepSeek-R1-0528",
        test_prompt: str = "Write a Python function to calculate fibonacci numbers."
    ) -> Dict[str, Dict[str, Any]]:
        """Benchmark different quantization methods"""
        
        results = {}
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # Test configurations
        configs = {
            "fp16": {
                "torch_dtype": torch.float16,
                "quantization_config": None
            },
            "4bit_nf4": {
                "torch_dtype": torch.float16,
                "quantization_config": QuantizationManager.get_4bit_config(quant_type="nf4")
            },
            "4bit_fp4": {
                "torch_dtype": torch.float16,
                "quantization_config": QuantizationManager.get_4bit_config(quant_type="fp4")
            },
            "8bit": {
                "torch_dtype": torch.float16,
                "quantization_config": QuantizationManager.get_8bit_config()
            }
        }
        
        for config_name, config in configs.items():
            try:
                logger.info(f"Testing {config_name} configuration")
                
                # Load model
                start_time = time.time()
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    **config
                )
                load_time = time.time() - start_time
                
                # Get memory usage
                if torch.cuda.is_available():
                    memory_used = torch.cuda.memory_allocated() / 1e9
                else:
                    memory_used = 0
                
                # Test generation
                inputs = tokenizer(test_prompt, return_tensors="pt")
                if torch.cuda.is_available():
                    inputs = {k: v.to(model.device) for k, v in inputs.items()}
                
                start_time = time.time()
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=100,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                generation_time = time.time() - start_time
                
                # Calculate tokens per second
                output_tokens = outputs.shape[1] - inputs['input_ids'].shape[1]
                tokens_per_second = output_tokens / generation_time
                
                results[config_name] = {
                    "load_time": load_time,
                    "memory_usage_gb": memory_used,
                    "generation_time": generation_time,
                    "tokens_per_second": tokens_per_second,
                    "output_tokens": output_tokens,
                    "success": True
                }
                
                # Cleanup
                del model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
            except Exception as e:
                logger.error(f"Failed to test {config_name}: {e}")
                results[config_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results

# Advanced quantization with custom configurations
class AdaptiveQuantization:
    """Adaptive quantization based on available resources"""
    
    def __init__(self, target_memory_gb: float = 16):
        self.target_memory_gb = target_memory_gb
    
    def get_optimal_config(self, model_size_gb: float) -> Dict[str, Any]:
        """Get optimal quantization config based on constraints"""
        
        if model_size_gb <= self.target_memory_gb:
            # No quantization needed
            return {
                "quantization_config": None,
                "torch_dtype": torch.float16,
                "strategy": "fp16"
            }
        elif model_size_gb <= self.target_memory_gb * 2:
            # 8-bit quantization
            return {
                "quantization_config": self.get_8bit_config(),
                "torch_dtype": torch.float16,
                "strategy": "8bit"
            }
        else:
            # 4-bit quantization
            return {
                "quantization_config": self.get_4bit_config(),
                "torch_dtype": torch.float16,
                "strategy": "4bit"
            }
    
    def estimate_memory_usage(self, model_size_gb: float, strategy: str) -> float:
        """Estimate memory usage for different strategies"""
        multipliers = {
            "fp16": 1.0,
            "8bit": 0.5,
            "4bit": 0.25
        }
        
        base_memory = model_size_gb * multipliers.get(strategy, 1.0)
        # Add overhead for activations and gradients
        return base_memory * 1.2

# Usage example
adaptive_quant = AdaptiveQuantization(target_memory_gb=16)
config = adaptive_quant.get_optimal_config(model_size_gb=25)
print(f"Optimal config: {config}")

estimated_memory = adaptive_quant.estimate_memory_usage(25, config["strategy"])
print(f"Estimated memory usage: {estimated_memory:.2f} GB")
```

### Memory Management and Caching

```python
# memory_management.py
import torch
import gc
import psutil
import os
import time
from typing import Dict, Any, Optional, List
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """Advanced memory management for DeepSeek R1-0528"""
    
    def __init__(self, max_memory_gb: Optional[float] = None):
        self.max_memory_gb = max_memory_gb or self._get_available_memory()
        self.memory_threshold = 0.9  # 90% threshold
        self.cleanup_callbacks = []
    
    def _get_available_memory(self) -> float:
        """Get available system memory in GB"""
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / 1e9
        else:
            return psutil.virtual_memory().total / 1e9
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get current memory usage information"""
        info = {}
        
        # System memory
        memory = psutil.virtual_memory()
        info.update({
            "system_total_gb": memory.total / 1e9,
            "system_used_gb": memory.used / 1e9,
            "system_available_gb": memory.available / 1e9,
            "system_percent": memory.percent
        })
        
        # GPU memory
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                allocated = torch.cuda.memory_allocated(i) / 1e9
                reserved = torch.cuda.memory_reserved(i) / 1e9
                total = torch.cuda.get_device_properties(i).total_memory / 1e9
                
                info.update({
                    f"gpu_{i}_allocated_gb": allocated,
                    f"gpu_{i}_reserved_gb": reserved,
                    f"gpu_{i}_total_gb": total,
                    f"gpu_{i}_free_gb": total - reserved
                })
        
        return info
    
    def cleanup_memory(self, aggressive: bool = False):
        """Perform memory cleanup"""
        # Run custom cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"Cleanup callback failed: {e}")
        
        # Python garbage collection
        gc.collect()
        
        # PyTorch GPU memory cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            if aggressive:
                # Force memory defragmentation
                torch.cuda.memory._dump_snapshot("memory_snapshot.pickle")
                torch.cuda.empty_cache()
    
    def register_cleanup_callback(self, callback):
        """Register a cleanup callback function"""
        self.cleanup_callbacks.append(callback)
    
    def memory_monitor(self, func):
        """Decorator to monitor memory usage of functions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Memory before
            memory_before = self.get_memory_info()
            
            try:
                result = func(*args, **kwargs)
                
                # Memory after
                memory_after = self.get_memory_info()
                
                # Log memory usage
                if torch.cuda.is_available():
                    gpu_used = memory_after.get("gpu_0_allocated_gb", 0) - memory_before.get("gpu_0_allocated_gb", 0)
                    logger.info(f"{func.__name__} used {gpu_used:.2f} GB GPU memory")
                
                system_used = memory_after["system_used_gb"] - memory_before["system_used_gb"]
                logger.info(f"{func.__name__} used {system_used:.2f} GB system memory")
                
                return result
                
            except Exception as e:
                # Cleanup on error
                self.cleanup_memory(aggressive=True)
                raise
        
        return wrapper
    
    def check_memory_threshold(self) -> bool:
        """Check if memory usage exceeds threshold"""
        memory_info = self.get_memory_info()
        
        # Check GPU memory
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                allocated = memory_info.get(f"gpu_{i}_allocated_gb", 0)
                total = memory_info.get(f"gpu_{i}_total_gb", 1)
                if allocated / total > self.memory_threshold:
                    return True
        
        # Check system memory
        if memory_info["system_percent"] > self.memory_threshold * 100:
            return True
        
        return False

class ResponseCache:
    """LRU cache for model responses"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.creation_times = {}
    
    def _generate_key(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate cache key from messages and parameters"""
        import hashlib
        import json
        
        # Create deterministic key
        cache_data = {
            "messages": messages,
            "params": {k: v for k, v in kwargs.items() if k in ["temperature", "top_p", "max_tokens"]}
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Get cached response"""
        key = self._generate_key(messages, **kwargs)
        
        if key in self.cache:
            # Check TTL
            if time.time() - self.creation_times[key] > self.ttl_seconds:
                self._remove_key(key)
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            return self.cache[key]
        
        return None
    
    def put(self, messages: List[Dict[str, str]], response: str, **kwargs):
        """Cache response"""
        key = self._generate_key(messages, **kwargs)
        
        # Remove oldest entries if cache is full
        while len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            self._remove_key(oldest_key)
        
        # Add new entry
        current_time = time.time()
        self.cache[key] = response
        self.access_times[key] = current_time
        self.creation_times[key] = current_time
    
    def _remove_key(self, key: str):
        """Remove key from all dictionaries"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.creation_times.pop(key, None)
    
    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        self.access_times.clear()
        self.creation_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": getattr(self, "_hit_count", 0) / max(getattr(self, "_total_requests", 1), 1),
            "oldest_entry_age": time.time() - min(self.creation_times.values()) if self.creation_times else 0
        }

# Usage example
memory_manager = MemoryManager()
response_cache = ResponseCache(max_size=500, ttl_seconds=1800)

# Register cleanup callback
def model_cleanup():
    """Custom cleanup function"""
    # Add your model-specific cleanup here
    pass

memory_manager.register_cleanup_callback(model_cleanup)

# Monitor memory usage
@memory_manager.memory_monitor
def generate_response(model, tokenizer, messages):
    """Example function with memory monitoring"""
    # Your generation logic here
    pass

# Check memory and cleanup if needed
if memory_manager.check_memory_threshold():
    logger.warning("Memory threshold exceeded, performing cleanup")
    memory_manager.cleanup_memory(aggressive=True)
```

## 6. Production-Ready Features

### Comprehensive Logging and Monitoring

```python
# monitoring.py
import logging
import time
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import threading

# Prometheus metrics
REQUEST_COUNT = Counter('deepseek_requests_total', 'Total requests', ['method', 'status'])
REQUEST_DURATION = Histogram('deepseek_request_duration_seconds', 'Request duration')
ACTIVE_REQUESTS = Gauge('deepseek_active_requests', 'Active requests')
MODEL_MEMORY_USAGE = Gauge('deepseek_memory_usage_bytes', 'Memory usage', ['device'])
TOKEN_COUNT = Counter('deepseek_tokens_total', 'Total tokens', ['type'])

@dataclass
class RequestMetrics:
    """Request metrics data structure"""
    request_id: str
    timestamp: float
    method: str
    messages: List[Dict[str, str]]
    response: str
    duration: float
    input_tokens: int
    output_tokens: int
    memory_usage: float
    status: str
    error: Optional[str] = None

class StructuredLogger:
    """Structured logging for DeepSeek operations"""
    
    def __init__(self, name: str, log_level: str = "INFO", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_request(self, metrics: RequestMetrics):
        """Log request with structured data"""
        log_data = {
            "event": "request_completed",
            "request_id": metrics.request_id,
            "timestamp": metrics.timestamp,
            "method": metrics.method,
            "duration": metrics.duration,
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "memory_usage": metrics.memory_usage,
            "status": metrics.status
        }
        
        if metrics.error:
            log_data["error"] = metrics.error
            self.logger.error(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))
    
    def log_model_event(self, event: str, data: Dict[str, Any]):
        """Log model-related events"""
        log_data = {
            "event": event,
            "timestamp": time.time(),
            **data
        }
        self.logger.info(json.dumps(log_data))

class MetricsCollector:
    """Collect and export metrics"""
    
    def __init__(self, export_port: int = 8080):
        self.export_port = export_port
        self.metrics_history: List[RequestMetrics] = []
        self.max_history = 10000
        self._lock = threading.Lock()
        
        # Start Prometheus metrics server
        start_http_server(export_port)
    
    def record_request(self, metrics: RequestMetrics):
        """Record request metrics"""
        with self._lock:
            # Update Prometheus metrics
            REQUEST_COUNT.labels(method=metrics.method, status=metrics.status).inc()
            REQUEST_DURATION.observe(metrics.duration)
            TOKEN_COUNT.labels(type='input').inc(metrics.input_tokens)
            TOKEN_COUNT.labels(type='output').inc(metrics.output_tokens)
            
            # Store in history
            self.metrics_history.append(metrics)
            
            # Trim history if needed
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history:]
    
    def update_memory_usage(self, device: str, usage_bytes: float):
        """Update memory usage metrics"""
        MODEL_MEMORY_USAGE.labels(device=device).set(usage_bytes)
    
    def get_statistics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get statistics for the specified time window"""
        cutoff_time = time.time() - (window_minutes * 60)
        
        with self._lock:
            recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"message": "No recent metrics available"}
        
        # Calculate statistics
        total_requests = len(recent_metrics)
        successful_requests = len([m for m in recent_metrics if m.status == "success"])
        failed_requests = total_requests - successful_requests
        
        durations = [m.duration for m in recent_metrics]
        input_tokens = [m.input_tokens for m in recent_metrics]
        output_tokens = [m.output_tokens for m in recent_metrics]
        
        return {
            "window_minutes": window_minutes,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "average_duration": sum(durations) / len(durations) if durations else 0,
            "total_input_tokens": sum(input_tokens),
            "total_output_tokens": sum(output_tokens),
            "average_input_tokens": sum(input_tokens) / len(input_tokens) if input_tokens else 0,
            "average_output_tokens": sum(output_tokens) / len(output_tokens) if output_tokens else 0,
            "requests_per_minute": total_requests / window_minutes if window_minutes > 0 else 0
        }

class HealthChecker:
    """Health monitoring for DeepSeek services"""
    
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes
        self.is_healthy = True
        self.health_details = {}
    
    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        current_time = time.time()
        
        # Skip if recently checked
        if current_time - self.last_health_check < self.health_check_interval:
            return {
                "status": "healthy" if self.is_healthy else "unhealthy",
                "last_check": self.last_health_check,
                "details": self.health_details
            }
        
        self.last_health_check = current_time
        health_results = {}
        
        try:
            # Test model inference
            test_input = "Hello, how are you?"
            inputs = self.tokenizer(test_input, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            start_time = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            inference_time = time.time() - start_time
            
            health_results["inference"] = {
                "status": "healthy",
                "response_time": inference_time,
                "test_successful": True
            }
            
        except Exception as e:
            health_results["inference"] = {
                "status": "unhealthy",
                "error": str(e),
                "test_successful": False
            }
        
        # Check memory usage
        try:
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1e9
                total = torch.cuda.get_device_properties(0).total_memory / 1e9
                usage_percent = (allocated / total) * 100
                
                health_results["memory"] = {
                    "status": "healthy" if usage_percent < 95 else "warning",
                    "gpu_allocated_gb": allocated,
                    "gpu_total_gb": total,
                    "usage_percent": usage_percent
                }
            else:
                import psutil
                memory = psutil.virtual_memory()
                health_results["memory"] = {
                    "status": "healthy" if memory.percent < 90 else "warning",
                    "system_usage_percent": memory.percent,
                    "available_gb": memory.available / 1e9
                }
                
        except Exception as e:
            health_results["memory"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Determine overall health
        self.is_healthy = all(
            result.get("status") in ["healthy", "warning"] 
            for result in health_results.values()
        )
        
        self.health_details = health_results
        
        return {
            "status": "healthy" if self.is_healthy else "unhealthy",
            "timestamp": current_time,
            "details": health_results
        }

# Usage example
logger = StructuredLogger("deepseek", log_level="INFO", log_file="deepseek.log")
metrics_collector = MetricsCollector(export_port=8080)

# Example request tracking
def track_request(func):
    """Decorator to track request metrics"""
    def wrapper(*args, **kwargs):
        request_id = f"req_{int(time.time() * 1000)}"
        start_time = time.time()
        
        ACTIVE_REQUESTS.inc()
        
        try:
            result = func(*args, **kwargs)
            
            # Create metrics
            metrics = RequestMetrics(
                request_id=request_id,
                timestamp=start_time,
                method=func.__name__,
                messages=kwargs.get("messages", []),
                response=result.get("response", ""),
                duration=time.time() - start_time,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                memory_usage=torch.cuda.memory_allocated() if torch.cuda.is_available() else 0,
                status="success"
            )
            
            # Log and record metrics
            logger.log_request(metrics)
            metrics_collector.record_request(metrics)
            
            return result
            
        except Exception as e:
            # Record error metrics
            metrics = RequestMetrics(
                request_id=request_id,
                timestamp=start_time,
                method=func.__name__,
                messages=kwargs.get("messages", []),
                response="",
                duration=time.time() - start_time,
                input_tokens=0,
                output_tokens=0,
                memory_usage=torch.cuda.memory_allocated() if torch.cuda.is_available() else 0,
                status="error",
                error=str(e)
            )
            
            logger.log_request(metrics)
            metrics_collector.record_request(metrics)
            
            raise
        
        finally:
            ACTIVE_REQUESTS.dec()
    
    return wrapper
```

### Error Handling and Retry Mechanisms

```python
# error_handling.py
import asyncio
import time
import random
from typing import Any, Callable, Optional, Dict, List
from functools import wraps
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Classification of error types"""
    NETWORK_ERROR = "network"
    MEMORY_ERROR = "memory"
    MODEL_ERROR = "model"
    TIMEOUT_ERROR = "timeout"
    RATE_LIMIT_ERROR = "rate_limit"
    UNKNOWN_ERROR = "unknown"

class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential"
    LINEAR_BACKOFF = "linear"
    FIXED_DELAY = "fixed"
    IMMEDIATE = "immediate"

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    retryable_errors: List[ErrorType] = None

    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = [
                ErrorType.NETWORK_ERROR,
                ErrorType.TIMEOUT_ERROR,
                ErrorType.RATE_LIMIT_ERROR
            ]

class DeepSeekError(Exception):
    """Base exception for DeepSeek operations"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = time.time()

class ModelLoadError(DeepSeekError):
    """Error during model loading"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorType.MODEL_ERROR, details)

class GenerationError(DeepSeekError):
    """Error during text generation"""
    def __init__(self, message: str, error_type: ErrorType = ErrorType.MODEL_ERROR, details: Dict[str, Any] = None):
        super().__init__(message, error_type, details)

class MemoryError(DeepSeekError):
    """Memory-related error"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorType.MEMORY_ERROR, details)

class ErrorClassifier:
    """Classify errors into types for appropriate handling"""
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorType:
        """Classify an exception into an error type"""
        error_str = str(error).lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ["connection", "network", "timeout", "unreachable"]):
            return ErrorType.NETWORK_ERROR
        
        # Memory-related errors
        if any(keyword in error_str for keyword in ["memory", "cuda out of memory", "oom"]):
            return ErrorType.MEMORY_ERROR
        
        # Rate limiting
        if any(keyword in error_str for keyword in ["rate limit", "too many requests", "quota"]):
            return ErrorType.RATE_LIMIT_ERROR
        
        # Timeout errors
        if any(keyword in error_str for keyword in ["timeout", "timed out"]):
            return ErrorType.TIMEOUT_ERROR
        
        # Model-specific errors
        if any(keyword in error_str for keyword in ["model", "generation", "tokenizer"]):
            return ErrorType.MODEL_ERROR
        
        return ErrorType.UNKNOWN_ERROR

class RetryHandler:
    """Handle retries with different strategies"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (2 ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        elif self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        else:  # IMMEDIATE
            delay = 0
        
        # Apply max delay limit
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter and delay > 0:
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if an error should be retried"""
        if attempt >= self.config.max_attempts:
            return False
        
        error_type = ErrorClassifier.classify_error(error)
        return error_type in self.config.retryable_errors
    
    def retry(self, func: Callable) -> Callable:
        """Decorator for adding retry logic"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(1, self.config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    last_error = e
                    
                    if not self.should_retry(e, attempt):
                        logger.error(f"Non-retryable error or max attempts reached: {e}")
                        raise
                    
                    delay = self.calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s")
                    
                    if delay > 0:
                        time.sleep(delay)
            
            # If we get here, all retries failed
            raise last_error
        
        return wrapper
    
    def async_retry(self, func: Callable) -> Callable:
        """Async decorator for adding retry logic"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(1, self.config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_error = e
                    
                    if not self.should_retry(e, attempt):
                        logger.error(f"Non-retryable error or max attempts reached: {e}")
                        raise
                    
                    delay = self.calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s")
                    
                    if delay > 0:
                        await asyncio.sleep(delay)
            
            # If we get here, all retries failed
            raise last_error
        
        return wrapper

class CircuitBreaker:
    """Circuit breaker pattern for preventing cascade failures"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable) -> Callable:
        """Decorator for circuit breaker"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise DeepSeekError(
                        "Circuit breaker is OPEN",
                        ErrorType.NETWORK_ERROR,
                        {"circuit_breaker_state": self.state}
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ErrorRecoveryManager:
    """Manage error recovery strategies"""
    
    def __init__(self):
        self.recovery_strategies = {}
        self.error_history = []
        self.max_history = 1000
    
    def register_recovery_strategy(self, error_type: ErrorType, strategy: Callable):
        """Register a recovery strategy for an error type"""
        self.recovery_strategies[error_type] = strategy
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Any:
        """Handle an error with appropriate recovery strategy"""
        error_type = ErrorClassifier.classify_error(error)
        
        # Record error in history
        self.error_history.append({
            "timestamp": time.time(),
            "error_type": error_type,
            "error_message": str(error),
            "context": context or {}
        })
        
        # Trim history
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
        
        # Apply recovery strategy
        if error_type in self.recovery_strategies:
            try:
                return self.recovery_strategies[error_type](error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
        
        # Re-raise if no recovery strategy or recovery failed
        raise error
    
    def get_error_statistics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get error statistics for the specified time window"""
        cutoff_time = time.time() - (window_minutes * 60)
        recent_errors = [e for e in self.error_history if e["timestamp"] > cutoff_time]
        
        if not recent_errors:
            return {"message": "No recent errors"}
        
        # Count by error type
        error_counts = {}
        for error in recent_errors:
            error_type = error["error_type"]
            error_counts[error_type.value] = error_counts.get(error_type.value, 0) + 1
        
        return {
            "window_minutes": window_minutes,
            "total_errors": len(recent_errors),
            "error_counts": error_counts,
            "error_rate": len(recent_errors) / window_minutes
        }

# Usage examples
def memory_recovery_strategy(error: Exception, context: Dict[str, Any]) -> None:
    """Recovery strategy for memory errors"""
    logger.info("Applying memory recovery strategy")
    
    # Clear GPU cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Force garbage collection
    import gc
    gc.collect()
    
    # Reduce batch size if available in context
    if "batch_size" in context:
        context["batch_size"] = max(1, context["batch_size"] // 2)
        logger.info(f"Reduced batch size to {context['batch_size']}")

def model_recovery_strategy(error: Exception, context: Dict[str, Any]) -> None:
    """Recovery strategy for model errors"""
    logger.info("Applying model recovery strategy")
    
    # Reload model if needed
    if "model_manager" in context:
        context["model_manager"].reload_model()

# Setup error handling
retry_config = RetryConfig(
    max_attempts=3,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay=1.0,
    max_delay=30.0
)

retry_handler = RetryHandler(retry_config)
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
error_recovery = ErrorRecoveryManager()

# Register recovery strategies
error_recovery.register_recovery_strategy(ErrorType.MEMORY_ERROR, memory_recovery_strategy)
error_recovery.register_recovery_strategy(ErrorType.MODEL_ERROR, model_recovery_strategy)

# Example usage
@retry_handler.retry
@circuit_breaker.call
def generate_with_error_handling(model, tokenizer, messages):
    """Example function with comprehensive error handling"""
    try:
        # Your generation logic here
        pass
    except Exception as e:
        # Let error recovery manager handle it
        error_recovery.handle_error(e, {"model": model, "tokenizer": tokenizer})
```

### Rate Limiting and Request Queuing

```python
# rate_limiting.py
import asyncio
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class QueueStrategy(Enum):
    """Queue management strategies"""
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    PRIORITY = "priority"  # Priority-based

@dataclass
class QueuedRequest:
    """Queued request data structure"""
    request_id: str
    timestamp: float
    priority: int
    func: Callable
    args: tuple
    kwargs: dict
    future: asyncio.Future

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket"""
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait for tokens to be available"""
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate

class SlidingWindowRateLimiter:
    """Sliding window rate limiter"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        with self._lock:
            now = time.time()
            
            # Remove old requests outside the window
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()
            
            # Check if we can add a new request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    def get_wait_time(self) -> float:
        """Get time to wait before next request is allowed"""
        with self._lock:
            if len(self.requests) < self.max_requests:
                return 0.0
            
            # Time until oldest request expires
            oldest_request = self.requests[0]
            return max(0.0, oldest_request + self.window_seconds - time.time())

class RequestQueue:
    """Async request queue with priority support"""
    
    def __init__(
        self,
        max_size: int = 1000,
        strategy: QueueStrategy = QueueStrategy.FIFO,
        timeout: float = 300.0
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.timeout = timeout
        self.queue = deque()
        self.processing = False
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition()
    
    async def enqueue(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 0
    ) -> Any:
        """Enqueue a request for processing"""
        kwargs = kwargs or {}
        request_id = f"req_{int(time.time() * 1000000)}"
        future = asyncio.Future()
        
        request = QueuedRequest(
            request_id=request_id,
            timestamp=time.time(),
            priority=priority,
            func=func,
            args=args,
            kwargs=kwargs,
            future=future
        )
        
        async with self._lock:
            if len(self.queue) >= self.max_size:
                raise Exception("Queue is full")
            
            # Add to queue based on strategy
            if self.strategy == QueueStrategy.PRIORITY:
                # Insert based on priority (higher priority first)
                inserted = False
                for i, existing_request in enumerate(self.queue):
                    if priority > existing_request.priority:
                        self.queue.insert(i, request)
                        inserted = True
                        break
                if not inserted:
                    self.queue.append(request)
            elif self.strategy == QueueStrategy.LIFO:
                self.queue.appendleft(request)
            else:  # FIFO
                self.queue.append(request)
        
        async with self._condition:
            self._condition.notify()
        
        # Wait for result with timeout
        try:
            return await asyncio.wait_for(future, timeout=self.timeout)
        except asyncio.TimeoutError:
            # Remove from queue if still there
            async with self._lock:
                try:
                    self.queue.remove(request)
                except ValueError:
                    pass  # Already processed
            raise Exception(f"Request {request_id} timed out")
    
    async def process_queue(self):
        """Process requests from the queue"""
        while True:
            request = None
            
            async with self._lock:
                if self.queue:
                    request = self.queue.popleft()
            
            if request:
                try:
                    # Execute the request
                    if asyncio.iscoroutinefunction(request.func):
                        result = await request.func(*request.args, **request.kwargs)
                    else:
                        result = request.func(*request.args, **request.kwargs)
                    
                    request.future.set_result(result)
                    
                except Exception as e:
                    request.future.set_exception(e)
            else:
                # Wait for new requests
                async with self._condition:
                    await self._condition.wait()
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "queue_size": len(self.queue),
            "max_size": self.max_size,
            "strategy": self.strategy.value,
            "oldest_request_age": time.time() - self.queue[0].timestamp if self.queue else 0
        }

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on system load"""
    
    def __init__(
        self,
        base_rate: float = 10.0,
        min_rate: float = 1.0,
        max_rate: float = 50.0,
        adaptation_factor: float = 0.1
    ):
        self.base_rate = base_rate
        self.current_rate = base_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.adaptation_factor = adaptation_factor
        
        self.token_bucket = TokenBucket(capacity=int(base_rate), refill_rate=base_rate)
        self.success_count = 0
        self.error_count = 0
        self.last_adaptation = time.time()
        self.adaptation_interval = 60.0  # Adapt every minute
    
    def request_permission(self) -> bool:
        """Request permission to proceed"""
        self._adapt_rate()
        return self.token_bucket.consume()
    
    def report_success(self):
        """Report successful request"""
        self.success_count += 1
    
    def report_error(self):
        """Report failed request"""
        self.error_count += 1
    
    def _adapt_rate(self):
        """Adapt rate based on success/error ratio"""
        now = time.time()
        
        if now - self.last_adaptation < self.adaptation_interval:
            return
        
        total_requests = self.success_count + self.error_count
        
        if total_requests > 0:
            success_rate = self.success_count / total_requests
            
            if success_rate > 0.95:  # High success rate, increase rate
                new_rate = min(self.max_rate, self.current_rate * (1 + self.adaptation_factor))
            elif success_rate < 0.8:  # Low success rate, decrease rate
                new_rate = max(self.min_rate, self.current_rate * (1 - self.adaptation_factor))
            else:
                new_rate = self.current_rate
            
            if new_rate != self.current_rate:
                self.current_rate = new_rate
                self.token_bucket = TokenBucket(
                    capacity=int(new_rate * 2),
                    refill_rate=new_rate
                )
                logger.info(f"Adapted rate limit to {new_rate:.2f} requests/second")
        
        # Reset counters
        self.success_count = 0
        self.error_count = 0
        self.last_adaptation = now

class DeepSeekRateLimitedService:
    """DeepSeek service with comprehensive rate limiting"""
    
    def __init__(
        self,
        model,
        tokenizer,
        requests_per_second: float = 5.0,
        max_concurrent: int = 10,
        queue_size: int = 100
    ):
        self.model = model
        self.tokenizer = tokenizer
        
        # Rate limiting
        self.rate_limiter = AdaptiveRateLimiter(base_rate=requests_per_second)
        self.sliding_window = SlidingWindowRateLimiter(
            max_requests=int(requests_per_second * 60),
            window_seconds=60
        )
        
        # Request queue
        self.request_queue = RequestQueue(
            max_size=queue_size,
            strategy=QueueStrategy.PRIORITY
        )
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Start queue processor
        asyncio.create_task(self.request_queue.process_queue())
    
    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        priority: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text with rate limiting and queuing"""
        
        # Check rate limits
        if not self.rate_limiter.request_permission():
            wait_time = self.rate_limiter.token_bucket.get_wait_time()
            raise Exception(f"Rate limit exceeded. Wait {wait_time:.2f} seconds")
        
        if not self.sliding_window.is_allowed():
            wait_time = self.sliding_window.get_wait_time()
            raise Exception(f"Window rate limit exceeded. Wait {wait_time:.2f} seconds")
        
        # Queue the request
        try:
            result = await self.request_queue.enqueue(
                func=self._generate_internal,
                args=(messages,),
                kwargs=kwargs,
                priority=priority
            )
            
            self.rate_limiter.report_success()
            return result
            
        except Exception as e:
            self.rate_limiter.report_error()
            raise
    
    async def _generate_internal(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Internal generation method with concurrency control"""
        
        async with self.semaphore:
            # Format messages
            prompt = self._format_messages(messages)
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=kwargs.get("max_length", 2048)
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate
            start_time = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get("max_new_tokens", 512),
                    temperature=kwargs.get("temperature", 0.7),
                    top_p=kwargs.get("top_p", 0.9),
                    do_sample=kwargs.get("do_sample", True),
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generation_time = time.time() - start_time
            
            # Decode response
            response_tokens = outputs[0][inputs['input_ids'].shape[1]:]
            response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
            return {
                "response": response,
                "generation_time": generation_time,
                "input_tokens": inputs['input_ids'].shape[1],
                "output_tokens": len(response_tokens)
            }
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for the model"""
        formatted = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                formatted += f"User: {content}\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n"
            elif role == "system":
                formatted += f"System: {content}\n"
        
        formatted += "Assistant: "
        return formatted
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        return {
            "rate_limiter": {
                "current_rate": self.rate_limiter.current_rate,
                "tokens_available": self.rate_limiter.token_bucket.tokens
            },
            "queue": self.request_queue.get_queue_stats(),
            "concurrent_requests": self.semaphore._value
        }

# Usage example
async def main():
    # Initialize service (assuming model and tokenizer are loaded)
    # service = DeepSeekRateLimitedService(model, tokenizer, requests_per_second=5.0)
    
    # Example requests
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    
    try:
        # High priority request
        result = await service.generate_text(messages, priority=10)
        print(f"Response: {result['response']}")
        
        # Get service statistics
        stats = service.get_service_stats()
        print(f"Service stats: {stats}")
        
    except Exception as e:
        print(f"Request failed: {e}")

# if __name__ == "__main__":
#     asyncio.run(main())
```

## 7. Troubleshooting Guide

### Common Issues and Solutions

```python
# troubleshooting.py
import torch
import psutil
import subprocess
import sys
import os
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SystemDiagnostics:
    """System diagnostics for DeepSeek deployment issues"""
    
    @staticmethod
    def check_cuda_installation() -> Dict[str, Any]:
        """Check CUDA installation and compatibility"""
        result = {
            "cuda_available": torch.cuda.is_available(),
            "issues": [],
            "recommendations": []
        }
        
        if not result["cuda_available"]:
            result["issues"].append("CUDA not available in PyTorch")
            result["recommendations"].extend([
                "Install CUDA-enabled PyTorch: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
                "Verify NVIDIA drivers are installed",
                "Check CUDA toolkit installation"
            ])
            return result
        
        # Check CUDA version
        try:
            cuda_version = torch.version.cuda
            result["cuda_version"] = cuda_version
            
            # Check driver version
            nvidia_smi = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
                capture_output=True, text=True
            )
            
            if nvidia_smi.returncode == 0:
                driver_version = nvidia_smi.stdout.strip()
                result["driver_version"] = driver_version
            else:
                result["issues"].append("nvidia-smi not available")
                result["recommendations"].append("Install NVIDIA drivers")
        
        except Exception as e:
            result["issues"].append(f"Error checking CUDA: {e}")
        
        # Check GPU memory
        try:
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                gpu_info = {
                    "name": props.name,
                    "total_memory_gb": props.total_memory / 1e9,
                    "compute_capability": f"{props.major}.{props.minor}"
                }
                result[f"gpu_{i}"] = gpu_info
                
                # Check if GPU has enough memory for DeepSeek
                if props.total_memory / 1e9 < 8:
                    result["issues"].append(f"GPU {i} has insufficient memory ({props.total_memory / 1e9:.1f} GB)")
                    result["recommendations"].append("Use quantization (4-bit or 8-bit) to reduce memory usage")
        
        except Exception as e:
            result["issues"].append(f"Error checking GPU properties: {e}")
        
        return result
    
    @staticmethod
    def check_memory_requirements() -> Dict[str, Any]:
        """Check system memory requirements"""
        memory = psutil.virtual_memory()
        
        result = {
            "total_memory_gb": memory.total / 1e9,
            "available_memory_gb": memory.available / 1e9,
            "memory_percent": memory.percent,
            "issues": [],
            "recommendations": []
        }
        
        # Check minimum requirements
        if memory.total / 1e9 < 16:
            result["issues"].append("Insufficient system RAM (minimum 16GB recommended)")
            result["recommendations"].append("Upgrade system RAM or use cloud instance with more memory")
        
        if memory.percent > 80:
            result["issues"].append("High memory usage detected")
            result["recommendations"].extend([
                "Close unnecessary applications",
                "Use swap file if available",
                "Consider using quantization to reduce memory usage"
            ])
        
        return result
    
    @staticmethod
    def check_dependencies() -> Dict[str, Any]:
        """Check required dependencies"""
        required_packages = {
            "torch": "2.0.0",
            "transformers": "4.37.0",
            "accelerate": "0.26.0",
            "bitsandbytes": "0.42.0"
        }
        
        result = {
            "installed_packages": {},
            "issues": [],
            "recommendations": []
        }
        
        for package, min_version in required_packages.items():
            try:
                module = __import__(package)
                version = getattr(module, "__version__", "unknown")
                result["installed_packages"][package] = version
                
                # Basic version check (simplified)
                if version == "unknown":
                    result["issues"].append(f"Cannot determine {package} version")
                
            except ImportError:
                result["issues"].append(f"Package {package} not installed")
                result["recommendations"].append(f"Install {package}: pip install {package}>={min_version}")
        
        return result
    
    @staticmethod
    def check_model_access() -> Dict[str, Any]:
        """Check if model can be accessed from Hugging Face"""
        result = {
            "model_accessible": False,
            "issues": [],
            "recommendations": []
        }
        
        try:
            from transformers import AutoTokenizer
            
            # Try to load tokenizer (lightweight check)
            tokenizer = AutoTokenizer.from_pretrained(
                "deepseek-ai/DeepSeek-R1-0528",
                trust_remote_code=True
            )
            result["model_accessible"] = True
            result["vocab_size"] = tokenizer.vocab_size
            
        except Exception as e:
            result["issues"].append(f"Cannot access model: {e}")
            result["recommendations"].extend([
                "Check internet connection",
                "Verify Hugging Face Hub access",
                "Try using HF_TOKEN environment variable if model requires authentication",
                "Check if model name is correct: deepseek-ai/DeepSeek-R1-0528"
            ])
        
        return result

class TroubleshootingGuide:
    """Comprehensive troubleshooting guide"""
    
    def __init__(self):
        self.diagnostics = SystemDiagnostics()
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run complete system diagnostics"""
        print("Running DeepSeek R1-0528 System Diagnostics...")
        print("=" * 50)
        
        results = {}
        
        # CUDA check
        print("1. Checking CUDA installation...")
        cuda_result = self.diagnostics.check_cuda_installation()
        results["cuda"] = cuda_result
        self._print_check_result("CUDA", cuda_result)
        
        # Memory check
        print("\n2. Checking memory requirements...")
        memory_result = self.diagnostics.check_memory_requirements()
        results["memory"] = memory_result
        self._print_check_result("Memory", memory_result)
        
        # Dependencies check
        print("\n3. Checking dependencies...")
        deps_result = self.diagnostics.check_dependencies()
        results["dependencies"] = deps_result
        self._print_check_result("Dependencies", deps_result)
        
        # Model access check
        print("\n4. Checking model access...")
        model_result = self.diagnostics.check_model_access()
        results["model_access"] = model_result
        self._print_check_result("Model Access", model_result)
        
        # Overall assessment
        print("\n" + "=" * 50)
        self._print_overall_assessment(results)
        
        return results
    
    def _print_check_result(self, check_name: str, result: Dict[str, Any]):
        """Print formatted check result"""
        issues = result.get("issues", [])
        recommendations = result.get("recommendations", [])
        
        if not issues:
            print(f"✅ {check_name}: OK")
        else:
            print(f"❌ {check_name}: Issues found")
            for issue in issues:
                print(f"   - {issue}")
            
            if recommendations:
                print("   Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
    
    def _print_overall_assessment(self, results: Dict[str, Any]):
        """Print overall system assessment"""
        total_issues = sum(len(result.get("issues", [])) for result in results.values())
        
        if total_issues == 0:
            print("🎉 System is ready for DeepSeek R1-0528 deployment!")
        else:
            print(f"⚠️  Found {total_issues} issues that need attention.")
            print("\nPriority fixes:")
            
            # Prioritize critical issues
            if results["cuda"]["issues"]:
                print("1. Fix CUDA installation (required for GPU acceleration)")
            
            if results["dependencies"]["issues"]:
                print("2. Install missing dependencies")
            
            if results["memory"]["issues"]:
                print("3. Address memory constraints")
            
            if results["model_access"]["issues"]:
                print("4. Resolve model access issues")

class CommonIssuesSolver:
    """Solutions for common deployment issues"""
    
    @staticmethod
    def solve_cuda_out_of_memory():
        """Solutions for CUDA OOM errors"""
        solutions = [
            "Use 4-bit quantization: quantization='4bit'",
            "Reduce max_length parameter",
            "Use gradient checkpointing: model.gradient_checkpointing_enable()",
            "Reduce batch size to 1",
            "Use CPU offloading: device_map='auto', max_memory={'0': '20GB', 'cpu': '30GB'}",
            "Clear CUDA cache: torch.cuda.empty_cache()",
            "Use model sharding across multiple GPUs"
        ]
        
        print("CUDA Out of Memory Solutions:")
        for i, solution in enumerate(solutions, 1):
            print(f"{i}. {solution}")
    
    @staticmethod
    def solve_slow_inference():
        """Solutions for slow inference"""
        solutions = [
            "Enable CUDA optimizations: torch.backends.cuda.matmul.allow_tf32 = True",
            "Use Flash Attention: pip install flash-attn",
            "Enable torch.compile() for PyTorch 2.0+",
            "Use vLLM for production inference",
            "Optimize batch size for your hardware",
            "Use tensor parallelism for multi-GPU setups",
            "Enable mixed precision: torch_dtype=torch.float16"
        ]
        
        print("Slow Inference Solutions:")
        for i, solution in enumerate(solutions, 1):
            print(f"{i}. {solution}")
    
    @staticmethod
    def solve_model_loading_errors():
        """Solutions for model loading errors"""
        solutions = [
            "Check internet connection and Hugging Face Hub access",
            "Use trust_remote_code=True parameter",
            "Set HF_TOKEN environment variable if needed",
            "Try downloading model manually: huggingface-cli download deepseek-ai/DeepSeek-R1-0528",
            "Use local model path if downloaded manually",
            "Check available disk space (model is ~50GB)",
            "Use low_cpu_mem_usage=True for large models"
        ]
        
        print("Model Loading Error Solutions:")
        for i, solution in enumerate(solutions, 1):
            print(f"{i}. {solution}")
    
    @staticmethod
    def solve_import_errors():
        """Solutions for import errors"""
        solutions = [
            "Update transformers: pip install transformers>=4.37.0",
            "Install missing dependencies: pip install accelerate bitsandbytes",
            "Use virtual environment to avoid conflicts",
            "Check Python version (3.8+ required)",
            "Reinstall PyTorch with CUDA support",
            "Clear pip cache: pip cache purge"
        ]
        
        print("Import Error Solutions:")
        for i, solution in enumerate(solutions, 1):
            print(f"{i}. {solution}")

# Interactive troubleshooting
def interactive_troubleshooting():
    """Interactive troubleshooting session"""
    guide = TroubleshootingGuide()
    solver = CommonIssuesSolver()
    
    print("DeepSeek R1-0528 Interactive Troubleshooting")
    print("=" * 45)
    
    while True:
        print("\nWhat issue are you experiencing?")
        print("1. Run full system diagnostics")
        print("2. CUDA out of memory errors")
        print("3. Slow inference speed")
        print("4. Model loading errors")
        print("5. Import/dependency errors")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            guide.run_full_diagnostics()
        elif choice == "2":
            solver.solve_cuda_out_of_memory()
        elif choice == "3":
            solver.solve_slow_inference()
        elif choice == "4":
            solver.solve_model_loading_errors()
        elif choice == "5":
            solver.solve_import_errors()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

# Quick diagnostic script
def quick_diagnostic():
    """Quick diagnostic check"""
    print("DeepSeek R1-0528 Quick Diagnostic")
    print("=" * 35)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8+ required")
        return
    else:
        print("✅ Python version OK")
    
    # Check PyTorch
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} installed")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.version.cuda}")
            print(f"✅ GPU count: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"   GPU {i}: {props.name} ({props.total_memory / 1e9:.1f} GB)")
        else:
            print("❌ CUDA not available")
    
    except ImportError:
        print("❌ PyTorch not installed")
        return
    
    # Check transformers
    try:
        import transformers
        print(f"✅ Transformers {transformers.__version__} installed")
    except ImportError:
        print("❌ Transformers not installed")
    
    # Check memory
    memory = psutil.virtual_memory()
    print(f"💾 System memory: {memory.total / 1e9:.1f} GB ({memory.percent:.1f}% used)")
    
    if memory.total / 1e9 < 16:
        print("⚠️  Low system memory (16GB+ recommended)")
    
    print("\nFor detailed diagnostics, run: python troubleshooting.py")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DeepSeek R1-0528 Troubleshooting")
    parser.add_argument("--quick", action="store_true", help="Run quick diagnostic")
    parser.add_argument("--interactive", action="store_true", help="Interactive troubleshooting")
    parser.add_argument("--full", action="store_true", help="Full system diagnostics")
    
    args = parser.parse_args()
    
    if args.quick:
        quick_diagnostic()
    elif args.interactive:
        interactive_troubleshooting()
    elif args.full:
        guide = TroubleshootingGuide()
        guide.run_full_diagnostics()
    else:
        print("Use --quick, --interactive, or --full")
```

## 8. Performance Benchmarking and Scaling

### Benchmarking Suite

```python
# benchmarking.py
import time
import torch
import psutil
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

@dataclass
class BenchmarkResult:
    """Benchmark result data structure"""
    test_name: str
    model_config: str
    input_tokens: int
    output_tokens: int
    generation_time: float
    tokens_per_second: float
    memory_usage_gb: float
    gpu_utilization: float
    success: bool
    error: Optional[str] = None

class DeepSeekBenchmark:
    """Comprehensive benchmarking suite for DeepSeek R1-0528"""
    
    def __init__(self, model, tokenizer, config_name: str = "default"):
        self.model = model
        self.tokenizer = tokenizer
        self.config_name = config_name
        self.results: List[BenchmarkResult] = []
    
    def benchmark_single_generation(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        runs: int = 5
    ) -> List[BenchmarkResult]:
        """Benchmark single text generation"""
        results = []
        
        for run in range(runs):
            try:
                # Clear cache before each run
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                
                # Tokenize input
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=2048
                )
                
                if torch.cuda.is_available():
                    inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                
                # Measure memory before generation
                memory_before = self._get_memory_usage()
                
                # Generate
                start_time = time.time()
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        temperature=temperature,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                
                generation_time = time.time() - start_time
                
                # Measure memory after generation
                memory_after = self._get_memory_usage()
                
                # Calculate metrics
                input_tokens = inputs['input_ids'].shape[1]
                output_tokens = outputs.shape[1] - input_tokens
                tokens_per_second = output_tokens / generation_time
                
                result = BenchmarkResult(
                    test_name=f"single_generation_run_{run}",
                    model_config=self.config_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    generation_time=generation_time,
                    tokens_per_second=tokens_per_second,
                    memory_usage_gb=memory_after,
                    gpu_utilization=self._get_gpu_utilization(),
                    success=True
                )
                
                results.append(result)
                
            except Exception as e:
                result = BenchmarkResult(
                    test_name=f"single_generation_run_{run}",
                    model_config=self.config_name,
                    input_tokens=0,
                    output_tokens=0,
                    generation_time=0,
                    tokens_per_second=0,
                    memory_usage_gb=0,
                    gpu_utilization=0,
                    success=False,
                    error=str(e)
                )
                results.append(result)
        
        self.results.extend(results)
        return results
    
    def benchmark_batch_generation(
        self,
        prompts: List[str],
        max_new_tokens: int = 256,
        temperature: float = 0.7
    ) -> BenchmarkResult:
        """Benchmark batch text generation"""
        try:
            # Clear cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            # Tokenize batch
            inputs = self.tokenizer(
                prompts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Measure memory before generation
            memory_before = self._get_memory_usage()
            
            # Generate batch
            start_time = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            
            generation_time = time.time() - start_time
            
            # Calculate metrics
            batch_size = len(prompts)
            total_input_tokens = inputs['input_ids'].numel()
            total_output_tokens = outputs.numel() - total_input_tokens
            tokens_per_second = total_output_tokens / generation_time
            
            result = BenchmarkResult(
                test_name=f"batch_generation_size_{batch_size}",
                model_config=self.config_name,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                generation_time=generation_time,
                tokens_per_second=tokens_per_second,
                memory_usage_gb=self._get_memory_usage(),
                gpu_utilization=self._get_gpu_utilization(),
                success=True
            )
            
        except Exception as e:
            result = BenchmarkResult(
                test_name=f"batch_generation_size_{len(prompts)}",
                model_config=self.config_name,
                input_tokens=0,
                output_tokens=0,
                generation_time=0,
                tokens_per_second=0,
                memory_usage_gb=0,
                gpu_utilization=0,
                success=False,
                error=str(e)
            )
        
        self.results.append(result)
        return result
    
    def benchmark_concurrent_requests(
        self,
        prompt: str,
        num_concurrent: int = 5,
        max_new_tokens: int = 128
    ) -> List[BenchmarkResult]:
        """Benchmark concurrent request handling"""
        results = []
        
        def single_request(request_id: int) -> BenchmarkResult:
            try:
                start_time = time.time()
                
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=2048
                )
                
                if torch.cuda.is_available():
                    inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                generation_time = time.time() - start_time
                
                input_tokens = inputs['input_ids'].shape[1]
                output_tokens = outputs.shape[1] - input_tokens
                
                return BenchmarkResult(
                    test_name=f"concurrent_request_{request_id}",
                    model_config=self.config_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    generation_time=generation_time,
                    tokens_per_second=output_tokens / generation_time,
                    memory_usage_gb=self._get_memory_usage(),
                    gpu_utilization=self._get_gpu_utilization(),
                    success=True
                )
                
            except Exception as e:
                return BenchmarkResult(
                    test_name=f"concurrent_request_{request_id}",
                    model_config=self.config_name,
                    input_tokens=0,
                    output_tokens=0,
                    generation_time=0,
                    tokens_per_second=0,
                    memory_usage_gb=0,
                    gpu_utilization=0,
                    success=False,
                    error=str(e)
                )
        
        # Run concurrent requests
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(single_request, i) for i in range(num_concurrent)]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        self.results.extend(results)
        return results
    
    def benchmark_different_lengths(
        self,
        base_prompt: str = "Write a detailed explanation about",
        topics: List[str] = None,
        max_tokens_list: List[int] = None
    ) -> List[BenchmarkResult]:
        """Benchmark generation with different output lengths"""
        if topics is None:
            topics = ["machine learning", "quantum computing", "climate change"]
        
        if max_tokens_list is None:
            max_tokens_list = [50, 128, 256, 512]
        
        results = []
        
        for topic in topics:
            prompt = f"{base_prompt} {topic}:"
            
            for max_tokens in max_tokens_list:
                try:
                    start_time = time.time()
                    
                    inputs = self.tokenizer(
                        prompt,
                        return_tensors="pt",
                        truncation=True,
                        max_length=2048
                    )
                    
                    if torch.cuda.is_available():
                        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=max_tokens,
                            temperature=0.7,
                            do_sample=True,
                            pad_token_id=self.tokenizer.eos_token_id
                        )
                    
                    generation_time = time.time() - start_time
                    
                    input_tokens = inputs['input_ids'].shape[1]
                    output_tokens = outputs.shape[1] - input_tokens
                    
                    result = BenchmarkResult(
                        test_name=f"length_test_{max_tokens}_tokens",
                        model_config=self.config_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        generation_time=generation_time,
                        tokens_per_second=output_tokens / generation_time,
                        memory_usage_gb=self._get_memory_usage(),
                        gpu_utilization=self._get_gpu_utilization(),
                        success=True
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    result = BenchmarkResult(
                        test_name=f"length_test_{max_tokens}_tokens",
                        model_config=self.config_name,
                        input_tokens=0,
                        output_tokens=0,
                        generation_time=0,
                        tokens_per_second=0,
                        memory_usage_gb=0,
                        gpu_utilization=0,
                        success=False,
                        error=str(e)
                    )
                    results.append(result)
        
        self.results.extend(results)
        return results
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in GB"""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1e9
        else:
            return psutil.virtual_memory().used / 1e9
    
    def _get_gpu_utilization(self) -> float:
        """Get GPU utilization percentage"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return utilization.gpu
        except:
            return 0.0
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        if not self.results:
            return {"error": "No benchmark results available"}
        
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        if not successful_results:
            return {"error": "No successful benchmark runs"}
        
        # Calculate statistics
        generation_times = [r.generation_time for r in successful_results]
        tokens_per_second = [r.tokens_per_second for r in successful_results]
        memory_usage = [r.memory_usage_gb for r in successful_results]
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": len(successful_results),
                "failed_tests": len(failed_results),
                "success_rate": len(successful_results) / len(self.results) * 100
            },
            "performance": {
                "avg_generation_time": statistics.mean(generation_times),
                "median_generation_time": statistics.median(generation_times),
                "min_generation_time": min(generation_times),
                "max_generation_time": max(generation_times),
                "std_generation_time": statistics.stdev(generation_times) if len(generation_times) > 1 else 0,
                
                "avg_tokens_per_second": statistics.mean(tokens_per_second),
                "median_tokens_per_second": statistics.median(tokens_per_second),
                "min_tokens_per_second": min(tokens_per_second),
                "max_tokens_per_second": max(tokens_per_second),
                
                "avg_memory_usage_gb": statistics.mean(memory_usage),
                "max_memory_usage_gb": max(memory_usage),
                "min_memory_usage_gb": min(memory_usage)
            },
            "model_config": self.config_name,
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report
    
    def save_results(self, filename: str):
        """Save benchmark results to file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Benchmark results saved to {filename}")
    
    def plot_results(self, save_path: Optional[str] = None):
        """Generate visualization of benchmark results"""
        if not self.results:
            print("No results to plot")
            return
        
        successful_results = [r for r in self.results if r.success]
        
        if not successful_results:
            print("No successful results to plot")
            return
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f"DeepSeek R1-0528 Benchmark Results ({self.config_name})", fontsize=16)
        
        # Tokens per second distribution
        tokens_per_second = [r.tokens_per_second for r in successful_results]
        axes[0, 0].hist(tokens_per_second, bins=20, alpha=0.7, edgecolor='black')
        axes[0, 0].set_xlabel("Tokens per Second")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].set_title("Generation Speed Distribution")
        
        # Generation time vs output tokens
        output_tokens = [r.output_tokens for r in successful_results]
        generation_times = [r.generation_time for r in successful_results]
        axes[0, 1].scatter(output_tokens, generation_times, alpha=0.7)
        axes[0, 1].set_xlabel("Output Tokens")
        axes[0, 1].set_ylabel("Generation Time (s)")
        axes[0, 1].set_title("Generation Time vs Output Length")
        
        # Memory usage over time
        test_indices = list(range(len(successful_results)))
        memory_usage = [r.memory_usage_gb for r in successful_results]
        axes[1, 0].plot(test_indices, memory_usage, marker='o', alpha=0.7)
        axes[1, 0].set_xlabel("Test Number")
        axes[1, 0].set_ylabel("Memory Usage (GB)")
        axes[1, 0].set_title("Memory Usage Over Tests")
        
        # Performance by test type
        test_types = {}
        for result in successful_results:
            test_type = result.test_name.split('_')[0]
            if test_type not in test_types:
                test_types[test_type] = []
            test_types[test_type].append(result.tokens_per_second)
        
        if len(test_types) > 1:
            axes[1, 1].boxplot(
                [test_types[t] for t in test_types.keys()],
                labels=list(test_types.keys())
            )
            axes[1, 1].set_ylabel("Tokens per Second")
            axes[1, 1].set_title("Performance by Test Type")
            axes[1, 1].tick_params(axis='x', rotation=45)
        else:
            axes[1, 1].text(0.5, 0.5, "Insufficient data\nfor comparison", 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title("Performance by Test Type")
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
        
        plt.show()

# Comprehensive benchmark suite
def run_comprehensive_benchmark(model, tokenizer, config_name: str = "default"):
    """Run comprehensive benchmark suite"""
    benchmark = DeepSeekBenchmark(model, tokenizer, config_name)
    
    print(f"Running comprehensive benchmark for {config_name}")
    print("=" * 50)
    
    # Test prompts
    test_prompts = [
        "Write a Python function to implement binary search.",
        "Explain the concept of machine learning in detail.",
        "Describe the process of photosynthesis step by step.",
        "What are the main differences between SQL and NoSQL databases?",
        "How does blockchain technology work?"
    ]
    
    # 1. Single generation benchmark
    print("1. Single generation benchmark...")
    for i, prompt in enumerate(test_prompts[:2]):  # Test with 2 prompts
        print(f"   Testing prompt {i+1}...")
        benchmark.benchmark_single_generation(prompt, max_new_tokens=256, runs=3)
    
    # 2. Batch generation benchmark
    print("2. Batch generation benchmark...")
    for batch_size in [2, 4]:
        print(f"   Testing batch size {batch_size}...")
        benchmark.benchmark_batch_generation(
            test_prompts[:batch_size],
            max_new_tokens=128
        )
    
    # 3. Different length benchmark
    print("3. Different output length benchmark...")
    benchmark.benchmark_different_lengths(
        base_prompt="Explain",
        topics=["artificial intelligence", "quantum physics"],
        max_tokens_list=[64, 128, 256]
    )
    
    # 4. Concurrent requests benchmark
    print("4. Concurrent requests benchmark...")
    benchmark.benchmark_concurrent_requests(
        "Write a short story about space exploration.",
        num_concurrent=3,
        max_new_tokens=100
    )
    
    # Generate and save report
    print("5. Generating report...")
    report = benchmark.generate_report()
    
    # Save results
    timestamp = int(time.time())
    results_file = f"benchmark_results_{config_name}_{timestamp}.json"
    benchmark.save_results(results_file)
    
    # Generate plots
    plot_file = f"benchmark_plots_{config_name}_{timestamp}.png"
    benchmark.plot_results(save_path=plot_file)
    
    # Print summary
    print("\nBenchmark Summary:")
    print(f"Total tests: {report['summary']['total_tests']}")
    print(f"Success rate: {report['summary']['success_rate']:.1f}%")
    print(f"Average tokens/second: {report['performance']['avg_tokens_per_second']:.2f}")
    print(f"Average memory usage: {report['performance']['avg_memory_usage_gb']:.2f} GB")
    
    return benchmark, report

# Usage example
if __name__ == "__main__":
    # This would be used with actual model and tokenizer
    # model = ... (your loaded model)
    # tokenizer = ... (your loaded tokenizer)
    # benchmark, report = run_comprehensive_benchmark(model, tokenizer, "4bit_quantized")
    pass
```

This completes the comprehensive DeepSeek R1-0528 Local Deployment Guide. The guide now includes:

1. **Complete Transformers Integration** - Both pipeline and direct model loading with advanced features
2. **Kaggle Notebook Implementation** - Cell-by-cell breakdown with memory optimization
3. **Production vLLM Server** - Full server implementation with monitoring and client libraries
4. **Docker Deployment** - Complete containerization with load balancing and monitoring
5. **Performance Optimization** - GPU acceleration, quantization, and memory management
6. **Production Features** - Logging, monitoring, error handling, and rate limiting
7. **Troubleshooting Guide** - Comprehensive diagnostics and solutions
8. **Benchmarking Suite** - Performance testing and analysis tools

The guide provides production-ready code examples, optimization techniques, and scaling strategies for all deployment scenarios you requested.