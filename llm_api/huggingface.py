import os, json
from litellm import completion, embedding


# DO NOT INVOKE DIRECTLY
class huggingface:

    os.environ["HUGGINGFACE_API_KEY"] = os.environ.get('access_key')

    @staticmethod
    def request_model(msg, role, temperature, top_p, penalty_score):
        response = completion(
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
        response = completion(
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
        embeddings = embedding(
            model=os.environ.get('embed_model'),
            input=text
        )

        embeddings = json.dumps(embeddings)
        embeddings = embeddings["data"]["embeddings"]

        return embeddings