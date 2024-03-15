

#sorry for not having an openai account... let me do the api for another platform as an example


import json
import requests
import os


def get_access_token():
    ak_and_sk = os.environ.get('access_key').split("|")
    BAIDU_CLOUD_API_KEY, BAIDU_CLOUD_SECRET_KEY = ak_and_sk[0], ak_and_sk[1]

    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": BAIDU_CLOUD_API_KEY, "client_secret": BAIDU_CLOUD_SECRET_KEY}
    access_token_cache = str(requests.post(url, params=params).json().get("access_token"))
    return access_token_cache


class qianfan:

    @staticmethod
    def request_model(msg):
        payload = json.dumps({"messages": msg})
        headers = {
            'Content-Type': 'application/json'
        }
        # structure of msg:
        # [
        #    {
        #        "role": "user",
        #        "content": "hello"
        #    },
        #    {
        #        "role": "assistant",
        #        "content": "hello, how can i assist you today?"
        #    },
        #
        #    ...
        # ]

        model = os.environ.get('model')
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}"
        url += "?access_token=" + get_access_token()

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.text
        response = json.loads(response)
        response = response["result"]    # let's discuss what to do when there is an exception, raise it out or return a specified value?

        return response                  # return value: a single string


    @staticmethod
    def request_submodel(msg):
        payload = json.dumps({"messages": msg})
        headers = {
            'Content-Type': 'application/json'
        }

        model = os.environ.get('submodel')
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}"
        url += "?access_token=" + get_access_token()

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.text
        response = json.loads(response)
        response = response["result"]    

        return response                  

    
    @staticmethod
    def request_embed_model(text: str):
        headers = {
            'Content-Type': 'application/json'
        }

        payload = json.dumps({"input": [text]})

        model = os.environ.get('embed_model')
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/{model}"
        url += "?access_token=" + get_access_token()

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.text
        response = json.loads(response)
        response = response["data"][0]["embedding"]

        return response     # a list of float64 nums. do we not need to specify the format of numbers?
