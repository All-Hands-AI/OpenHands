import os

from llm_api.qianfan import qianfan

#apis = {"openai": openai, "claude": claude, "qianfan": qianfan, ...}
apis = {"qianfan": qianfan}

api = apis[os.environ.get('platform')]

def request_model(msg):
    return api.request_model(msg)

def request_submodel(msg):
    return api.request_submodel(msg)

def request_embed_model(msg):
    return api.request_embed_model(msg)