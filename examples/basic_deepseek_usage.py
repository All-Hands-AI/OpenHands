#!/usr/bin/env python3
"""
Basic DeepSeek R1-0528 usage example

This script demonstrates how to load and use the DeepSeek R1-0528 model
for text generation with basic configuration.
"""

import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Any

def check_system_requirements():
    """Check system requirements and capabilities"""
    print("System Requirements Check:")
    print("=" * 30)
    
    # Python version
    import sys
    print(f"Python version: {sys.version}")
    
    # PyTorch version
    print(f"PyTorch version: {torch.__version__}")
    
    # CUDA availability
    if torch.cuda.is_available():
        print(f"CUDA available: Yes")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i}: {props.name} ({props.total_memory / 1e9:.1f} GB)")
    else:
        print("CUDA available: No (CPU mode only)")
    
    # Memory info
    import psutil
    memory = psutil.virtual_memory()
    print(f"System RAM: {memory.total / 1e9:.1f} GB ({memory.percent:.1f}% used)")
    
    print()

def load_model_and_tokenizer(use_quantization: bool = True) -> tuple:
    """Load DeepSeek R1-0528 model and tokenizer"""
    print("Loading DeepSeek R1-0528...")
    print("=" * 30)
    
    model_name = "deepseek-ai/DeepSeek-R1-0528"
    
    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )
    print(f"✓ Tokenizer loaded (vocab size: {tokenizer.vocab_size})")
    
    # Configure model loading
    model_kwargs = {
        "trust_remote_code": True,
        "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
        "low_cpu_mem_usage": True,
    }
    
    # Add device mapping for GPU
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"
        
        # Add quantization for memory efficiency
        if use_quantization:
            from transformers import BitsAndBytesConfig
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            model_kwargs["quantization_config"] = quantization_config
            print("Using 4-bit quantization for memory efficiency")
    
    # Load model
    print("Loading model (this may take a few minutes)...")
    start_time = time.time()
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        **model_kwargs
    )
    
    load_time = time.time() - start_time
    print(f"✓ Model loaded in {load_time:.2f} seconds")
    
    # Print memory usage
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        print(f"GPU memory allocated: {allocated:.2f} GB")
    
    return model, tokenizer

def generate_text(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> Dict[str, Any]:
    """Generate text using the model"""
    print(f"Generating response for: '{prompt[:50]}...'")
    
    # Tokenize input
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    )
    
    # Move to GPU if available
    if torch.cuda.is_available() and hasattr(model, 'device'):
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    # Generate
    start_time = time.time()
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    generation_time = time.time() - start_time
    
    # Decode response
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the generated part (remove input prompt)
    generated_text = full_response[len(prompt):].strip()
    
    # Calculate metrics
    input_tokens = inputs['input_ids'].shape[1]
    output_tokens = outputs.shape[1] - input_tokens
    tokens_per_second = output_tokens / generation_time
    
    return {
        "prompt": prompt,
        "generated_text": generated_text,
        "full_response": full_response,
        "generation_time": generation_time,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tokens_per_second": tokens_per_second
    }

def run_examples(model, tokenizer):
    """Run example generations"""
    print("Running Example Generations:")
    print("=" * 40)
    
    examples = [
        {
            "prompt": "Write a Python function to calculate the factorial of a number:",
            "max_tokens": 200
        },
        {
            "prompt": "Explain the concept of machine learning in simple terms:",
            "max_tokens": 150
        },
        {
            "prompt": "What are the main differences between Python and JavaScript?",
            "max_tokens": 180
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print("-" * 20)
        
        result = generate_text(
            model,
            tokenizer,
            example["prompt"],
            max_new_tokens=example["max_tokens"]
        )
        
        print(f"Prompt: {result['prompt']}")
        print(f"Response: {result['generated_text']}")
        print(f"Generation time: {result['generation_time']:.2f}s")
        print(f"Speed: {result['tokens_per_second']:.2f} tokens/second")
        print(f"Tokens: {result['input_tokens']} input, {result['output_tokens']} output")

def interactive_mode(model, tokenizer):
    """Interactive chat mode"""
    print("\nInteractive Mode:")
    print("=" * 20)
    print("Enter your prompts (type 'quit' to exit)")
    
    while True:
        try:
            prompt = input("\nYou: ").strip()
            
            if prompt.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not prompt:
                continue
            
            result = generate_text(
                model,
                tokenizer,
                prompt,
                max_new_tokens=256,
                temperature=0.7
            )
            
            print(f"DeepSeek: {result['generated_text']}")
            print(f"({result['generation_time']:.2f}s, {result['tokens_per_second']:.1f} tok/s)")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main function"""
    print("DeepSeek R1-0528 Basic Usage Example")
    print("=" * 40)
    
    # Check system requirements
    check_system_requirements()
    
    try:
        # Load model and tokenizer
        model, tokenizer = load_model_and_tokenizer(use_quantization=True)
        
        # Run examples
        run_examples(model, tokenizer)
        
        # Interactive mode
        interactive_mode(model, tokenizer)
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have enough memory (16GB+ RAM recommended)")
        print("2. Try using quantization: use_quantization=True")
        print("3. Check CUDA installation if using GPU")
        print("4. Ensure internet connection for model download")
    
    finally:
        # Cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

if __name__ == "__main__":
    main()