# Running SWE-bench with E2B Runtime at Scale

This guide explains how to use E2B as the runtime for OpenHands when running SWE-benchmark evaluations at scale.

## Overview

E2B provides cloud-based sandboxes that can be used as an alternative to Docker containers for running SWE-bench evaluations. This is particularly useful for:
- Running evaluations in cloud environments without Docker
- Scaling evaluations across multiple machines
- Using self-hosted E2B instances for better control and performance

## Prerequisites

1. E2B API key (from e2b.dev or your self-hosted instance)
2. OpenHands repository with E2B runtime installed
3. Python environment with all dependencies

## Configuration

### 1. Basic Setup

```bash
# Set E2B API key
export E2B_API_KEY="your-api-key-here"

# For self-hosted E2B instances
export E2B_DOMAIN="your-e2b-domain.com"  # Optional: only for self-hosted

# Specify E2B as the runtime
export RUNTIME=e2b
```

### 2. Running SWE-bench with E2B

```bash
# Basic command structure
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    <model_config> \
    <git_version> \
    <agent> \
    <eval_limit> \
    <max_iter> \
    <num_workers> \
    <dataset> \
    <split>

# Example: Running SWE-bench_Lite with GPT-4
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    llm.eval_gpt4_1106_preview \
    HEAD \
    CodeActAgent \
    300 \
    30 \
    1 \
    "princeton-nlp/SWE-bench_Lite" \
    test
```

### 3. Scaling with Parallel Workers

```bash
# Run with 16 parallel workers
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    llm.eval_gpt4_1106_preview \
    HEAD \
    CodeActAgent \
    300 \
    30 \
    16 \
    "princeton-nlp/SWE-bench_Lite" \
    test
```

## Advanced Configuration

### 1. Resource Management

E2B sandboxes can be configured with different resource allocations:

```bash
# Set default resource factor for all instances
export DEFAULT_RUNTIME_RESOURCE_FACTOR=2.0

# For specific instances, create a resource mapping file
# evaluation/benchmarks/swe_bench/resource/swe_bench_lite.json
```

### 2. LLM Configuration

Create a `config.toml` file:

```toml
[llm.eval_gpt4_1106_preview]
model = "gpt-4-1106-preview"
api_key = "your-openai-api-key"
temperature = 0.0

[llm.eval_claude]
model = "claude-3-opus-20240229"
api_key = "your-anthropic-api-key"
temperature = 0.0
```

### 3. Evaluation Options

```bash
# Enable iterative evaluation (up to 3 attempts per instance)
export ITERATIVE_EVAL_MODE=true

# Enable hint text for debugging
export USE_HINT_TEXT=true

# Skip instances that exceed maximum retries
export EVAL_SKIP_MAXIMUM_RETRIES_EXCEEDED=true

# Use custom instruction template
export INSTRUCTION_TEMPLATE_NAME=custom_template
```

## Best Practices for Scale

### 1. Batch Processing

Split your evaluation into batches to manage costs and resources:

```bash
# Evaluate specific instances
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    llm.eval_gpt4_1106_preview \
    HEAD \
    CodeActAgent \
    300 \
    30 \
    16 \
    "princeton-nlp/SWE-bench_Lite" \
    test \
    --instance-ids instance1,instance2,instance3
```

### 2. Monitoring and Logging

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Set output directory
export EVAL_OUTPUT_PATH=/path/to/results

# Enable detailed error tracking
export EVAL_SAVE_ERROR_LOGS=true
```

### 3. Cost Optimization

- E2B charges per sandbox hour, so optimize your evaluation time
- Use parallel workers to reduce total wall-clock time
- Configure appropriate timeouts to avoid hanging instances
- Clean up sandboxes after evaluation

### 4. Reliability

```bash
# Enable retry mechanism for transient failures
export EVAL_MAX_RETRIES=3

# Set connection timeout
export E2B_CONNECTION_TIMEOUT=300

# Enable checkpoint saving for resume capability
export EVAL_SAVE_CHECKPOINTS=true
```

## E2B-Specific Considerations

### Advantages:
1. **No Docker Required**: Runs in cloud environments without Docker
2. **Automatic Scaling**: E2B handles infrastructure management
3. **Isolated Environments**: Each instance gets a fresh sandbox
4. **Persistent Storage**: Sandboxes can be reused across evaluations
5. **Built-in Security**: Sandboxed execution environment

### Limitations:
1. **No Interactive Browser**: Browser-based tasks won't work
2. **No VSCode Integration**: Can't use VSCode features
3. **No Local File Mounting**: Files must be copied to sandbox
4. **Network Latency**: API calls add overhead compared to local Docker

## Example: Large-Scale Evaluation

Here's a complete example for running a large-scale evaluation:

```bash
#!/bin/bash

# Configuration
export E2B_API_KEY="your-api-key"
export E2B_DOMAIN="your-custom-domain.com"  # For self-hosted
export RUNTIME=e2b

# Evaluation settings
export ITERATIVE_EVAL_MODE=true
export EVAL_SKIP_MAXIMUM_RETRIES_EXCEEDED=true
export DEFAULT_RUNTIME_RESOURCE_FACTOR=2.0

# Logging
export LOG_LEVEL=INFO
export EVAL_OUTPUT_PATH="./results/swe_bench_$(date +%Y%m%d_%H%M%S)"
mkdir -p $EVAL_OUTPUT_PATH

# Run evaluation with 32 parallel workers
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    llm.eval_gpt4_1106_preview \
    HEAD \
    CodeActAgent \
    500 \
    30 \
    32 \
    "princeton-nlp/SWE-bench" \
    test \
    2>&1 | tee $EVAL_OUTPUT_PATH/evaluation.log

# Process results
python evaluation/benchmarks/swe_bench/scripts/eval_infer.py \
    --output_dir $EVAL_OUTPUT_PATH \
    --dataset "princeton-nlp/SWE-bench" \
    --split test
```

## Troubleshooting

### Common Issues:

1. **Sandbox Creation Failures**
   - Check E2B API key is valid
   - Verify E2B domain (for self-hosted)
   - Check E2B service status

2. **Timeout Errors**
   - Increase `E2B_CONNECTION_TIMEOUT`
   - Check network connectivity
   - Reduce parallel workers if rate-limited

3. **Resource Limits**
   - Monitor E2B quota/limits
   - Adjust `DEFAULT_RUNTIME_RESOURCE_FACTOR`
   - Use batching for large evaluations

4. **Evaluation Failures**
   - Check logs in `EVAL_OUTPUT_PATH`
   - Enable `USE_HINT_TEXT` for debugging
   - Run single instance to isolate issues

## Performance Tuning

1. **Optimize Parallel Workers**: Find the sweet spot between parallelism and API rate limits
2. **Cache Docker Images**: E2B can cache base images for faster startup
3. **Reuse Sandboxes**: Use `attach_to_existing=true` for sequential evaluations
4. **Batch Similar Instances**: Group instances by repository for better caching

## Conclusion

E2B runtime provides a scalable alternative to Docker for running SWE-bench evaluations. While it has some limitations compared to local Docker execution, its cloud-native design makes it ideal for large-scale evaluations in distributed environments.

For the latest updates and additional features, check:
- E2B documentation: https://e2b.dev/docs
- OpenHands evaluation docs: `/evaluation/README.md`
- SWE-bench specific docs: `/evaluation/benchmarks/swe_bench/README.md`