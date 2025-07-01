# Model-Specific Settings

This document provides recommendations for model-specific settings to optimize performance and reliability when using different LLM providers with OpenHands.

## Gemini Models

### Timeout Settings

Gemini models may require longer timeouts than other models, especially for complex prompts. We recommend setting a timeout of at least 120 seconds when using Gemini models:

```toml
[llm]
# Model to use
model = "gemini/gemini-2.5-pro-preview-06-05"
# Timeout for the API (in seconds)
timeout = 120
```

In our testing, we found that:
- Simple prompts typically complete in 5-10 seconds
- Complex prompts with code analysis or detailed reasoning can take 30-60+ seconds
- The default timeout (30 seconds) is often insufficient for complex prompts

### Safety Settings

Gemini models support custom safety settings, which can be configured as follows:

```toml
[llm]
model = "gemini/gemini-2.5-pro-preview-06-05"
safety_settings = [
  { "category" = "HARM_CATEGORY_HARASSMENT", "threshold" = "BLOCK_NONE" },
  { "category" = "HARM_CATEGORY_HATE_SPEECH", "threshold" = "BLOCK_NONE" },
  { "category" = "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold" = "BLOCK_NONE" },
  { "category" = "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold" = "BLOCK_NONE" }
]
```

## Claude Models

Claude models generally work well with the default settings, but you may want to adjust the following:

```toml
[llm]
model = "anthropic/claude-3-5-sonnet-20241022"
# Increase max tokens for longer responses
max_output_tokens = 4096
```

## GPT Models

For OpenAI GPT models, consider the following settings:

```toml
[llm]
model = "gpt-4o"
# Adjust temperature for more deterministic responses
temperature = 0.0
```

## General Recommendations

For all models, we recommend:

1. Setting appropriate retry parameters:
   ```toml
   [llm]
   # Number of retries to attempt when an operation fails with the LLM
   num_retries = 8
   # Minimum wait time (in seconds) between retry attempts
   retry_min_wait = 15
   # Maximum wait time (in seconds) between retry attempts
   retry_max_wait = 120
   # Multiplier for exponential backoff calculation
   retry_multiplier = 2.0
   ```

2. Adjusting token limits based on your use case:
   ```toml
   [llm]
   # Maximum number of input tokens
   max_input_tokens = 16000
   # Maximum number of output tokens
   max_output_tokens = 4000
   ```