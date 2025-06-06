#!/usr/bin/env python3
"""
Memory-optimized DeepSeek R1-0528 usage example

This script demonstrates advanced memory optimization techniques
for running DeepSeek R1-0528 on systems with limited resources.
"""

import torch
import gc
import psutil
import time
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Dict, Any, Optional

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def get_memory_info() -> Dict[str, float]:
        """Get current memory usage"""
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
    
    @staticmethod
    def optimize_system():
        """Apply system-level optimizations"""
        print("Applying memory optimizations...")
        
        # Python garbage collection
        gc.collect()
        
        # PyTorch optimizations
        if torch.cuda.is_available():
            # Clear CUDA cache
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            # Enable optimizations
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            
            # Set memory fraction
            torch.cuda.set_per_process_memory_fraction(0.95)
            
            # Configure memory allocation
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
        
        print("✓ Memory optimizations applied")
    
    @staticmethod
    def print_memory_usage():
        """Print current memory usage"""
        info = MemoryOptimizer.get_memory_info()
        
        print("Memory Usage:")
        print(f"  System: {info['system_used_gb']:.2f}/{info['system_total_gb']:.2f} GB ({info['system_percent']:.1f}%)")
        
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                allocated = info.get(f"gpu_{i}_allocated_gb", 0)
                total = info.get(f"gpu_{i}_total_gb", 0)
                percent = (allocated / total * 100) if total > 0 else 0
                print(f"  GPU {i}: {allocated:.2f}/{total:.2f} GB ({percent:.1f}%)")

class OptimizedDeepSeekModel:
    """Memory-optimized DeepSeek model wrapper"""
    
    def __init__(self, quantization_strategy: str = "4bit"):
        self.model = None
        self.tokenizer = None
        self.quantization_strategy = quantization_strategy
        self.memory_optimizer = MemoryOptimizer()
        
    def get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Get quantization configuration based on strategy"""
        if self.quantization_strategy == "4bit":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_quant_storage=torch.uint8
            )
        elif self.quantization_strategy == "8bit":
            return BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                llm_int8_enable_fp32_cpu_offload=True
            )
        else:
            return None
    
    def get_optimal_device_map(self) -> Dict[str, str]:
        """Calculate optimal device mapping"""
        if not torch.cuda.is_available():
            return {"": "cpu"}
        
        # Get available GPU memory
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        
        if gpu_memory >= 24:
            # High-end GPU - can handle most of the model
            return {
                "": "cuda:0"
            }
        elif gpu_memory >= 16:
            # Mid-range GPU - use CPU offloading
            return {
                "model.embed_tokens": "cuda:0",
                "model.layers.0": "cuda:0",
                "model.layers.1": "cuda:0",
                "model.layers.2": "cuda:0",
                "model.layers.3": "cuda:0",
                "model.layers.4": "cuda:0",
                "model.layers.5": "cuda:0",
                "model.layers.6": "cuda:0",
                "model.layers.7": "cuda:0",
                "model.norm": "cpu",
                "lm_head": "cpu"
            }
        else:
            # Low VRAM - aggressive CPU offloading
            return {
                "model.embed_tokens": "cuda:0",
                "model.layers.0": "cuda:0",
                "model.layers.1": "cuda:0",
                "model.norm": "cpu",
                "lm_head": "cpu"
            }
    
    def load_model(self):
        """Load model with memory optimizations"""
        print("Loading DeepSeek R1-0528 with memory optimizations...")
        
        # Apply system optimizations
        self.memory_optimizer.optimize_system()
        
        # Print initial memory state
        print("\nMemory before loading:")
        self.memory_optimizer.print_memory_usage()
        
        model_name = "deepseek-ai/DeepSeek-R1-0528"
        
        # Load tokenizer
        print("\nLoading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        print("✓ Tokenizer loaded")
        
        # Configure model loading
        quantization_config = self.get_quantization_config()
        device_map = self.get_optimal_device_map()
        
        # Determine max memory allocation
        max_memory = {}
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            max_memory["0"] = f"{int(gpu_memory * 0.8)}GB"  # Use 80% of GPU memory
        
        # Add CPU memory limit
        system_memory = psutil.virtual_memory().total / 1e9
        max_memory["cpu"] = f"{int(system_memory * 0.6)}GB"  # Use 60% of system memory
        
        print(f"Using quantization: {self.quantization_strategy}")
        print(f"Device map: {device_map}")
        print(f"Max memory: {max_memory}")
        
        # Load model
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
            "low_cpu_mem_usage": True,
            "device_map": device_map,
            "max_memory": max_memory,
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        
        start_time = time.time()
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **model_kwargs
        )
        load_time = time.time() - start_time
        
        print(f"✓ Model loaded in {load_time:.2f} seconds")
        
        # Print memory after loading
        print("\nMemory after loading:")
        self.memory_optimizer.print_memory_usage()
    
    def generate_with_memory_monitoring(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text with memory monitoring"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Memory before generation
        memory_before = self.memory_optimizer.get_memory_info()
        
        # Tokenize with length limit
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=min(2048, 4096 - max_new_tokens)  # Leave room for generation
        )
        
        # Move to appropriate device
        if torch.cuda.is_available():
            # Only move to GPU if model has GPU components
            try:
                inputs = {k: v.to("cuda:0") for k, v in inputs.items()}
            except:
                # Fallback to CPU if GPU placement fails
                pass
        
        # Generate with memory cleanup
        start_time = time.time()
        
        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=kwargs.get("top_p", 0.9),
                    do_sample=kwargs.get("do_sample", True),
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True,  # Enable KV cache for efficiency
                )
            
            generation_time = time.time() - start_time
            
            # Decode response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = full_response[len(prompt):].strip()
            
            # Calculate metrics
            input_tokens = inputs['input_ids'].shape[1]
            output_tokens = outputs.shape[1] - input_tokens
            tokens_per_second = output_tokens / generation_time
            
            # Memory after generation
            memory_after = self.memory_optimizer.get_memory_info()
            
            return {
                "prompt": prompt,
                "generated_text": generated_text,
                "generation_time": generation_time,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tokens_per_second": tokens_per_second,
                "memory_before": memory_before,
                "memory_after": memory_after
            }
            
        finally:
            # Cleanup after generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
    
    def cleanup(self):
        """Clean up model and free memory"""
        if self.model:
            del self.model
            self.model = None
        
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        
        # Aggressive cleanup
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        print("✓ Model cleanup completed")

def benchmark_quantization_strategies():
    """Benchmark different quantization strategies"""
    print("Benchmarking Quantization Strategies")
    print("=" * 40)
    
    strategies = ["4bit", "8bit", "none"]
    test_prompt = "Explain the concept of artificial intelligence:"
    
    results = {}
    
    for strategy in strategies:
        print(f"\nTesting {strategy} quantization...")
        
        try:
            model = OptimizedDeepSeekModel(quantization_strategy=strategy)
            
            # Load model
            start_time = time.time()
            model.load_model()
            load_time = time.time() - start_time
            
            # Test generation
            result = model.generate_with_memory_monitoring(
                test_prompt,
                max_new_tokens=100,
                temperature=0.7
            )
            
            # Get memory usage
            memory_info = model.memory_optimizer.get_memory_info()
            gpu_memory = memory_info.get("gpu_0_allocated_gb", 0)
            
            results[strategy] = {
                "load_time": load_time,
                "generation_time": result["generation_time"],
                "tokens_per_second": result["tokens_per_second"],
                "gpu_memory_gb": gpu_memory,
                "success": True
            }
            
            print(f"✓ {strategy}: {result['tokens_per_second']:.2f} tok/s, {gpu_memory:.2f} GB")
            
            # Cleanup
            model.cleanup()
            
        except Exception as e:
            print(f"✗ {strategy} failed: {e}")
            results[strategy] = {"success": False, "error": str(e)}
    
    # Print comparison
    print("\nQuantization Comparison:")
    print("-" * 30)
    for strategy, result in results.items():
        if result["success"]:
            print(f"{strategy:>8}: {result['tokens_per_second']:>6.2f} tok/s, {result['gpu_memory_gb']:>6.2f} GB")
        else:
            print(f"{strategy:>8}: Failed")

def main():
    """Main function"""
    print("DeepSeek R1-0528 Memory-Optimized Usage")
    print("=" * 40)
    
    # Check system capabilities
    memory_info = MemoryOptimizer.get_memory_info()
    print(f"System Memory: {memory_info['system_total_gb']:.1f} GB")
    
    if torch.cuda.is_available():
        gpu_memory = memory_info.get("gpu_0_total_gb", 0)
        print(f"GPU Memory: {gpu_memory:.1f} GB")
        
        # Recommend quantization strategy
        if gpu_memory >= 24:
            recommended = "none or 8bit"
        elif gpu_memory >= 12:
            recommended = "8bit"
        else:
            recommended = "4bit"
        
        print(f"Recommended quantization: {recommended}")
    else:
        print("GPU: Not available (CPU mode)")
        recommended = "4bit"
    
    print()
    
    try:
        # Option 1: Benchmark different strategies
        print("1. Benchmark quantization strategies")
        print("2. Interactive mode with optimized model")
        choice = input("Choose option (1 or 2): ").strip()
        
        if choice == "1":
            benchmark_quantization_strategies()
        else:
            # Interactive mode
            print(f"\nLoading model with {recommended} quantization...")
            
            # Use most memory-efficient strategy
            strategy = "4bit" if "4bit" in recommended else "8bit"
            model = OptimizedDeepSeekModel(quantization_strategy=strategy)
            model.load_model()
            
            print("\nInteractive mode (type 'quit' to exit):")
            
            while True:
                try:
                    prompt = input("\nYou: ").strip()
                    
                    if prompt.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not prompt:
                        continue
                    
                    result = model.generate_with_memory_monitoring(
                        prompt,
                        max_new_tokens=200,
                        temperature=0.7
                    )
                    
                    print(f"DeepSeek: {result['generated_text']}")
                    print(f"({result['generation_time']:.2f}s, {result['tokens_per_second']:.1f} tok/s)")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
            
            # Cleanup
            model.cleanup()
    
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure you have enough memory (16GB+ recommended)")
        print("2. Try 4-bit quantization for lower memory usage")
        print("3. Close other applications to free memory")
        print("4. Check CUDA installation if using GPU")

if __name__ == "__main__":
    main()