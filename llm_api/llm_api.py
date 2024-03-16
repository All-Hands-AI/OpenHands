import os

api = os.environ.get('platform')

if api == "openai":
    from openai import openai
    api = openai
elif api == "claude":
    from claude import claude
    api = claude
elif api == "qwen":
    from qwen import qwen
    api = qwen
elif api == "qianfan":
    from qianfan import qianfan
    api = qianfan

def request_model(msg):
    return api.request_model(msg)

def request_submodel(msg):
    return api.request_submodel(msg)

def request_embed_model(msg):
    return api.request_embed_model(msg)