import os
import litellm


'''
Available Platforms:
["openai", "azure", "sagemaker", "bedrock", "vertex_ai", "palm", "gemini", "mistral", "cloudflare", "cohere", "anthropic", "huggingface", 
 "replicate", "together_ai", "openrouter", "ai21", "baseten", "vllm", "nlp_cloud", "aleph_alpha", "petals", "ollama", "deepinfra", 
 "perplexity", "groq", "anyscale"]
'''
os.environ["platform"]    = ""    # specify the platform
os.environ["model"]       = ""    # specify the main model to use
os.environ["submodel"]    = ""    # specify a model with lower cost and reduced intelligence, to save money for some easier tasks

os.environ["cost"],    os.environ["cost_currency"]    = "1.0", "USD"    # cost is the price per 1000 tokens
os.environ["subcost"], os.environ["subcost_currency"] = "1.0", "CNY"


'''
Available Platforms:
["openai", "azure", "sagemaker", "bedrock", "mistral", "cohere", "huggingface", "voyage", "xinference"]
'''
os.environ["embed_platform"] = ""    # specify the platform for embedding model.
os.environ["embed_model"]    = ""    # model for embedding

os.environ["embed_cost"], os.environ["embed_cost_currency"] = "1.0", "EUR"


# OpenAI
os.environ["OPENAI_API_KEY"] = "your-api-key"

# Azure OpenAI
os.environ["AZURE_API_KEY"] = "" # "my-azure-api-key"
os.environ["AZURE_API_BASE"] = "" # "https://example-endpoint.openai.azure.com"
os.environ["AZURE_API_VERSION"] = "" # "2023-05-15"
# optional
os.environ["AZURE_AD_TOKEN"] = ""
os.environ["AZURE_API_TYPE"] = ""

# AWS Sagemaker
'''
    !pip install boto3
''' 
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""
os.environ["AWS_REGION_NAME"] = ""

# AWS Bedrock
'''
    pip install boto3>=1.28.57
''' 
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""
os.environ["AWS_REGION_NAME"] = ""

# VertexAI - Google [Gemini, Model Garden]
litellm.vertex_project = "hardy-device-38811" # Your Project ID
litellm.vertex_location = "us-central1"  # proj location
 
# PaLM API - Google
os.environ['PALM_API_KEY'] = ""

# Gemini - Google AI Studio
os.environ['GEMINI_API_KEY'] = ""

# Mistral AI API
os.environ['MISTRAL_API_KEY'] = ""

# Cloudflare Workers AI
os.environ['CLOUDFLARE_API_KEY'] = "3dnSGlxxxx"
os.environ['CLOUDFLARE_ACCOUNT_ID'] = "03xxxxx"

# Cohere
os.environ["COHERE_API_KEY"] = ""

# Anthropic
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

# Huggingface
os.environ["HUGGINGFACE_API_KEY"] = "huggingface_api_key"
os.environ["API_BASE"] = "https://my-endpoint.huggingface.cloud"

# Replicate
os.environ["REPLICATE_API_KEY"] = ""

# Together AI
os.environ["TOGETHERAI_API_KEY"] = "your-api-key"

# OpenRouter
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["OR_SITE_URL"] = "" # optional
os.environ["OR_APP_NAME"] = "" # optional

# AI21
os.environ["AI21_API_KEY"] = "your-api-key"

# Baseten
os.environ["BASETEN_API_KEY"] = ""

# VLLM
'''
    pip install litellm vllm
'''
os.environ["API_BASE"] = "https://hosted-vllm-api.co"

# NLP Cloud
os.environ["NLP_CLOUD_API_KEY"] = "your-api-key"

# Aleph Alpha
os.environ["ALEPHALPHA_API_KEY"] = ""

# Petals
'''
    pip install git+https://github.com/bigscience-workshop/petals
'''

# Ollama
os.environ["API_BASE"] = "http://localhost:11434"

# DeepInfra
os.environ['DEEPINFRA_API_KEY'] = ""

# Perplexity AI (pplx-api)
os.environ['PERPLEXITYAI_API_KEY'] = ""

# Groq
os.environ['GROQ_API_KEY'] = ""

# Anyscale
os.environ['ANYSCALE_API_KEY'] = ""

# Voyage AI
os.environ['VOYAGE_API_KEY'] = ""

# Xinference [Xorbits Inference]
os.environ['XINFERENCE_API_BASE'] = "http://127.0.0.1:9997/v1"
os.environ['XINFERENCE_API_KEY'] = "anything" #[optional] no api key required