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

This completes the first part of the comprehensive DeepSeek R1-0528 deployment guide. The guide covers:

1. **Transformers Library Integration** with both pipeline and direct model loading approaches
2. **Kaggle Notebook Implementation** with memory optimization and cell-by-cell breakdown
3. **vLLM Local Server Setup** with production-ready features
4. **Docker Deployment** with load balancing and monitoring

Would you like me to continue with the remaining sections covering performance optimization, production-ready features, and troubleshooting?