import os, json
from litellm import completion, embedding


ak_sak_rn = os.environ.get('access_key').split("|")
os.environ["AZURE_API_KEY"] = ak_sak_rn[0]
os.environ["AZURE_API_BASE"] = ak_sak_rn[1]
os.environ["AZURE_API_VERSION"] = "2023-05-15"


class azure:

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