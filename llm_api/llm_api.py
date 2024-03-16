import os
import importlib

platform = os.environ.get('platform')

api_module = importlib.import_module(f"llm_api.{platform}")
api = getattr(api_module, platform)

def request_model(msg):
    return api.request_model(msg)

def request_submodel(msg):
    return api.request_submodel(msg)

def request_embed_model(msg):
    return api.request_embed_model(msg)