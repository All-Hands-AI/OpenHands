import asyncio
import nest_asyncio

from g4f.client import Client

from opendevin.llm.ollama_client import Ollama
client = Client()

ollam = Ollama()

def get_completion(messages,
            stop=["</execute>"],
            temperature=0.0,
            seed=42):
        nest_asyncio.apply()
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stop=stop,
            temperature=temperature,
            seed=seed
        )
        msgcontent = res.choices[0].message.content
        return {
                'choices': [
                    {
                        'message': {
                            'content': msgcontent
                        }
                    }
                ]
        }

def get_ollam_completion(messages,
            stop=["</execute>"],
            temperature=0.0,
            seed=42):
        nest_asyncio.apply()
        msgcontent = ollam.inference(messages, stop, temperature, seed)
        return {
                'choices': [
                    {
                        'message': {
                            'content': msgcontent
                        }
                    }
                ]
        }
    
    