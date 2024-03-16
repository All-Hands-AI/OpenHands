import os, json
from litellm import completion, embedding

class cohere:

    os.environ["COHERE_API_KEY"] = os.environ.get('access_key')

    @staticmethod
    def request_model(msg):
        response = completion(
            model=os.environ.get('model'),
            messages=msg
        )
        answer = response.choices[0].message.content
        return answer

    
    @staticmethod
    def request_submodel(msg):
        response = completion(
            model=os.environ.get('submodel'),
            messages=msg
        )
        answer = response.choices[0].message.content
        return answer


    @staticmethod
    def request_embed_model(text: str):
        embeddings = embedding(
            model=os.environ.get('embed_model'),
            input=text
        )

        embeddings = json.dumps(embeddings)
        embeddings = embeddings["data"]["embeddings"]

        return embeddings