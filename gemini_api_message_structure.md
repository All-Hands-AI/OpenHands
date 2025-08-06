# Gemini 2.5 Pro API Message Structure and Configuration

This document provides comprehensive information about the Gemini API message structure, system instructions, and generationConfig based on official Google documentation.

## Key Findings

### System Instructions
- **System instructions are NOT part of the contents array**
- **System instructions are sent as a separate `systemInstruction` field**
- **No specific ordering requirement for system messages within contents**

### Message Structure
- **Contents array contains conversation messages in chronological order**
- **Each message has a `role` (user/model) and `parts` array**
- **System instructions are separate from conversation flow**

## API Request Structure

### Basic Structure
```json
{
  "systemInstruction": {
    "parts": [
      {
        "text": "You are a helpful assistant."
      }
    ]
  },
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "Hello, how are you?"
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.7,
    "topP": 0.8,
    "topK": 40,
    "thinkingConfig": {
      "includeThoughts": true
    }
  }
}
```

## System Instructions

### Key Points
- System instructions are **separate from the contents array**
- They are sent in the `systemInstruction` field at the root level
- System instructions guide the overall behavior of the model

### REST API Example
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "system_instruction": {
      "parts": [
        {
          "text": "You are a cat. Your name is Neko."
        }
      ]
    },
    "contents": [
      {
        "parts": [
          {
            "text": "Hello there"
          }
        ]
      }
    ]
  }'
```

### Python SDK Example
```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a cat. Your name is Neko."
    ),
    contents="Hello there"
)
```

### JavaScript SDK Example
```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

const response = await ai.models.generateContent({
  model: "gemini-2.5-flash",
  contents: "Hello there",
  config: {
    systemInstruction: "You are a cat. Your name is Neko.",
  },
});
```

## Multi-turn Conversations (Chat)

### Message Ordering
- **No requirement for system messages to be first in contents**
- **Contents array follows chronological conversation order**
- **Roles alternate between "user" and "model"**

### REST API Chat Example
```bash
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "Hello"
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "Great to meet you. What would you like to know?"
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "I have two dogs in my house. How many paws are in my house?"
          }
        ]
      }
    ]
  }'
```

### Python Chat Example
```python
from google import genai

client = genai.Client()
chat = client.chats.create(model="gemini-2.5-flash")

response = chat.send_message("I have 2 dogs in my house.")
print(response.text)

response = chat.send_message("How many paws are in my house?")
print(response.text)

for message in chat.get_history():
    print(f'role - {message.role}: {message.parts[0].text}')
```

### JavaScript Chat Example
```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

const chat = ai.chats.create({
  model: "gemini-2.5-flash",
  history: [
    {
      role: "user",
      parts: [{ text: "Hello" }],
    },
    {
      role: "model",
      parts: [{ text: "Great to meet you. What would you like to know?" }],
    },
  ],
});

const response1 = await chat.sendMessage({
  message: "I have 2 dogs in my house.",
});

const response2 = await chat.sendMessage({
  message: "How many paws are in my house?",
});
```

## Generation Configuration

### Basic Configuration
```json
{
  "generationConfig": {
    "temperature": 1.0,
    "topP": 0.8,
    "topK": 10,
    "stopSequences": ["Title"]
  }
}
```

### Thinking Configuration (Gemini 2.5)
```json
{
  "generationConfig": {
    "temperature": 0.7,
    "thinkingConfig": {
      "thinkingBudget": 0,
      "includeThoughts": true
    }
  }
}
```

### REST API with Generation Config
```bash
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works"
          }
        ]
      }
    ],
    "generationConfig": {
      "stopSequences": ["Title"],
      "temperature": 1.0,
      "topP": 0.8,
      "topK": 10,
      "thinkingConfig": {
        "includeThoughts": true
      }
    }
  }'
```

### Python with Generation Config
```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["Explain how AI works"],
    config=types.GenerateContentConfig(
        temperature=0.1,
        thinking_config=types.ThinkingConfig(
            include_thoughts=True
        )
    )
)
```

### JavaScript with Generation Config
```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

const response = await ai.models.generateContent({
  model: "gemini-2.5-flash",
  contents: "Explain how AI works",
  config: {
    temperature: 0.1,
    thinkingConfig: {
      includeThoughts: true,
    },
  },
});
```

## Complete Example with All Features

### REST API Complete Example
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "systemInstruction": {
      "parts": [
        {
          "text": "You are a helpful AI assistant specialized in explaining complex topics clearly."
        }
      ]
    },
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "Hello, I need help understanding machine learning."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "Hello! I would be happy to help you understand machine learning. What specific aspect would you like to explore?"
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "Can you explain neural networks in simple terms?"
          }
        ]
      }
    ],
    "generationConfig": {
      "temperature": 0.7,
      "topP": 0.8,
      "topK": 40,
      "maxOutputTokens": 1000,
      "thinkingConfig": {
        "includeThoughts": true
      }
    }
  }'
```

## Key Takeaways

1. **System Instructions**: Separate field (`systemInstruction`), not part of `contents`
2. **Message Ordering**: No requirement for system messages to be first in `contents`
3. **Conversation Flow**: `contents` array follows chronological order with alternating user/model roles
4. **Generation Config**: Separate `generationConfig` object for model parameters
5. **Thinking Mode**: Available in Gemini 2.5 models via `thinkingConfig`

## References

All information in this document is sourced from official Google Gemini API documentation:

- **Text Generation Guide**: https://ai.google.dev/gemini-api/docs/text-generation
- **API Reference**: https://ai.google.dev/api/generate-content
- **System Instructions**: Examples from text generation guide showing `systemInstruction` as separate field
- **Chat Examples**: Multi-turn conversation examples from official documentation
- **Generation Config**: Configuration examples from official REST API documentation
- **Thinking Configuration**: Gemini 2.5 thinking examples from official documentation

Each code example and API structure shown above is directly from Google's official documentation and represents the current (as of January 2025) API specification.