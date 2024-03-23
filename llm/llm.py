## Added all the three clients 
from enum import Enum
from anthropic import Anthropic
import openai
import httpx
import ollama

# Placeholder functions for external dependencies
def get_encoding(string):
    return f"Encoded string: {string}"

# Use ALL_CAPS naming convention for constants
TOKEN_USAGE = 0
TIKTOKEN_ENC = get_encoding("cl100k_base")

class Model(Enum):
    CLAUDE_3_OPUS = ("Claude 3 Opus", "claude-3-opus-20240229")
    CLAUDE_3_SONNET = ("Claude 3 Sonnet", "claude-3-sonnet-20240229")
    CLAUDE_3_HAIKU = ("Claude 3 Haiku", "claude-3-haiku-20240307")
    GPT_4_TURBO = ("GPT-4 Turbo", "gpt-4-0125-preview")
    GPT_3_5 = ("GPT-3.5", "gpt-3.5-turbo-0125")
    
    OLLAMA_MODELS = [
        (
            model[0].split(":")[0],
            model[1],
        )
        for model in [
            ("Model 1:ollama", "ollama_model_1"),
            ("Model 2:ollama", "ollama_model_2")
        ]
    ]

class Config:
    @staticmethod
    def get_claude_api_key():
        # Replace 'YOUR_CLAUDE_API_KEY' with your actual Claude API key
        return 'YOUR_OPENAI_API_KEY'

    @staticmethod
    def get_openai_api_key():
        # Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
        return 'YOUR_OPENAI_API_KEY'

class LLM:
    def __init__(self, model_id: str = None):
        self.model_id = model_id
        self.TOKEN_USAGE = 0

    def list_models(self) -> list[tuple[str, str]]:
        return [model.value for model in Model if model.name != "OLLAMA_MODELS"] + list(
            Model.OLLAMA_MODELS.value
        )

    def model_id_to_enum_mapping(self):
        models_mapping = {model.value[1]: model for model in Model if model.name != "OLLAMA_MODELS"}
        ollama_models = {model[1]: "OLLAMA_MODELS" for model in Model.OLLAMA_MODELS.value}
        models_mapping.update(ollama_models)
        return models_mapping

    def update_global_token_usage(self, string: str):
        # Use the placeholder function get_encoding to encode the string
        encoded_string = get_encoding(string)
        self.TOKEN_USAGE += len(encoded_string)
        print(f"Token usage: {self.TOKEN_USAGE}")

    def inference(self, prompt: str) -> str:
        self.update_global_token_usage(prompt)
        
        model = self.model_id_to_enum_mapping()[self.model_id]

        if model == "OLLAMA_MODELS":
            return self.ollama_inference(prompt)
        elif "CLAUDE" in str(model):
            return self.claude_inference(prompt)
        elif "GPT" in str(model):
            return self.openai_inference(prompt)
        else:
            raise ValueError(f"Model {model} not supported")

    def ollama_inference(self, prompt: str) -> str:
        try:
            response = ollama.generate(
                model=self.model_id,
                prompt=prompt.strip()
            )
            return response['response']
        except httpx.ConnectError:
            print("Ollama server not running, please start the server to use models from Ollama.")
        except Exception as e:
            print(f"Failed to use Ollama model: {e}")
            return ""

    def claude_inference(self, prompt: str) -> str:
        try:
            config = Config()
            api_key = config.get_claude_api_key()
            client = Anthropic(api_key=api_key)
            message = client.messages.create(
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt.strip(),
                    }
                ],
                model=self.model_id,
            )
            return message.content[0].text
        except Exception as e:
            print(f"Failed to use Claude model: {e}")
            return ""

    def openai_inference(self, prompt: str) -> str:
        try:
            config = Config()
            api_key = config.get_openai_api_key()
            client = openai.OpenAI(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt.strip(),
                    }
                ],
                model=self.model_id,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Failed to use OpenAI model: {e}")
            return ""

# Example usage
llm = LLM("claude-3-opus-20240229")
print(llm.list_models())

#print(llm.inference("Test prompt"))
# Test with a prompt asking about the Prime Minister of India
prompt = "Who is the Prime Minister of India?"
print(llm.inference(prompt))