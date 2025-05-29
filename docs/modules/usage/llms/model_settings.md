# Model-Specific Settings

This guide explains model-specific settings that can be configured in OpenHands, especially safety settings for different LLM providers.

## Safety Settings

Some LLM providers offer safety settings that can be adjusted to control the model's responses. OpenHands supports configuring these settings through the `safety_settings` parameter in the config.toml file.

### Mistral AI Safety Settings

Mistral AI models support safety settings with the following categories and thresholds:

- **Categories**:
  - `hate`: Controls filtering of content related to hate speech
  - `harassment`: Controls filtering of harassing content
  - `sexual`: Controls filtering of sexually explicit content
  - `dangerous`: Controls filtering of dangerous content (like instructions for harmful activities)

- **Thresholds**:
  - `none`: No filtering
  - `low`: Minimal filtering (default for code generation use cases)
  - `medium`: Moderate filtering
  - `high`: Maximum filtering

#### Example Configuration

```toml
[llm.mistral]
model = "mistral-large"
api_key = "your-api-key"
safety_settings = [
  { category = "hate", threshold = "low" },
  { category = "harassment", threshold = "low" },
  { category = "sexual", threshold = "low" },
  { category = "dangerous", threshold = "low" }
]
```

### Gemini Safety Settings

Gemini models support safety settings with different categories and thresholds compared to Mistral:

- **Categories**:
  - `HARM_CATEGORY_HARASSMENT`: Controls filtering of harassing content
  - `HARM_CATEGORY_HATE_SPEECH`: Controls filtering of hate speech
  - `HARM_CATEGORY_SEXUALLY_EXPLICIT`: Controls filtering of sexually explicit content
  - `HARM_CATEGORY_DANGEROUS_CONTENT`: Controls filtering of dangerous content

- **Thresholds**:
  - `BLOCK_NONE`: No filtering
  - `BLOCK_LOW_AND_ABOVE`: Low and above filtering
  - `BLOCK_MEDIUM_AND_ABOVE`: Medium and above filtering
  - `BLOCK_ONLY_HIGH`: Only high filtering
  - `BLOCK_ALL`: Block all content in this category

#### Example Configuration

```toml
[llm.gemini]
model = "gemini-2.5-pro"
api_key = "your-api-key"
safety_settings = [
  { category = "HARM_CATEGORY_HARASSMENT", threshold = "BLOCK_NONE" },
  { category = "HARM_CATEGORY_HATE_SPEECH", threshold = "BLOCK_NONE" },
  { category = "HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold = "BLOCK_NONE" },
  { category = "HARM_CATEGORY_DANGEROUS_CONTENT", threshold = "BLOCK_NONE" }
]
```

## Default Settings

If no safety settings are provided for models that support them:

- For Mistral AI models, OpenHands applies a default setting with `low` thresholds for all categories.
- For other models, their default provider settings are used.

## Impact on Code Generation

Overly restrictive safety settings can sometimes prevent models from generating certain types of code. For development tasks in OpenHands, it's recommended to use lower safety thresholds to avoid unnecessary restrictions on code generation.

## Recommended Settings for Development

For most development tasks, the following settings are recommended:

### For Mistral:
```toml
safety_settings = [
  { category = "hate", threshold = "low" },
  { category = "harassment", threshold = "low" },
  { category = "sexual", threshold = "low" },
  { category = "dangerous", threshold = "low" }
]
```

### For Gemini:
```toml
safety_settings = [
  { category = "HARM_CATEGORY_HARASSMENT", threshold = "BLOCK_NONE" },
  { category = "HARM_CATEGORY_HATE_SPEECH", threshold = "BLOCK_NONE" },
  { category = "HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold = "BLOCK_NONE" },
  { category = "HARM_CATEGORY_DANGEROUS_CONTENT", threshold = "BLOCK_NONE" }
]
```
