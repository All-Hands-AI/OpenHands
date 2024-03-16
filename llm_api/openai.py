import openai as OpenAI
import os, json

OpenAI.api_key = os.environ.get('access_key')

class openai:

    @staticmethod
    def request_model(msg):
        response = OpenAI.ChatCompletion.create(
            model=os.environ.get('model'),
            messages=msg
        )
        answer = response.choices[0].message.content
        return answer

    
    @staticmethod
    def request_submodel(msg):
        response = OpenAI.ChatCompletion.create(
            model=os.environ.get('submodel'),
            messages=msg
        )
        answer = response.choices[0].message.content
        return answer


    @staticmethod
    def request_embed_model(text: str):
        embeddings = OpenAI.Embedding.create(
            model=os.environ.get('embed_model'),
            input=text
        )

        embeddings = json.dumps(embeddings)
        embeddings = embeddings["data"]["embeddings"]

        return embeddings