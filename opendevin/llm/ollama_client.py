from ollama import Client

client = Client(host="http://127.0.0.1:11434")
print(client)

class Ollama:
    def inference(self, messages, stop=["</execute>"],
            temperature=0.0,
            seed=42) -> str:
        try:
            print(f"messages: {messages}")
            response = client.chat(model="llama2", messages=messages, options={"stop": stop, "temperature": temperature, "seed": seed})
            print(f"response: {response}")
            return response['message']['content']
        except Exception as e:
            print(f"Error during model inference: {e}")
            raise e

