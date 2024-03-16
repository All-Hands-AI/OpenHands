import openai as OpenAI
import os, json


# DO NOT INVOKE DIRECTLY
class openai:

    OpenAI.api_key = os.environ.get('access_key')

    @staticmethod
    def request_model(msg, role, temperature, top_p, penalty_score):
        response = OpenAI.ChatCompletion.create(
            model=os.environ.get('model'),
            messages=msg,
            temperature=temperature,
            top_p=top_p,
            penalty_score=penalty_score
        )
        answer = response.choices[0].message.content
        return answer

    
    @staticmethod
    def request_submodel(msg, role, temperature, top_p, penalty_score):
        response = OpenAI.ChatCompletion.create(
            model=os.environ.get('submodel'),
            messages=msg,
            temperature=temperature,
            top_p=top_p,
            penalty_score=penalty_score
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