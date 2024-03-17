import config   # import config.py to init env vars

from llm_api.llm_api import request_model, request_submodel, request_embed_model
from llm_api.llm_statistics import llm_statistics

print(
    request_model(
        [{
            "role": "user", 
            "content": "hello"
        }]
    )
)

print(
    request_model(
        [{
            "role": "user", 
            "content": "hello"
        }]
    , temperature=0.5, top_p=0.5, n=4, stream=True, stop=" ", max_tokens=10, presence_penalty=1.5, frequency_penalty=1.5, seed=12345)
)

print(
    request_submodel(
        [{
            "role": "user", 
            "content": "hello"
        }]
    )
)

print(
    request_submodel(
        [{
            "role": "user", 
            "content": "hello"
        }]
    , temperature=0.5, top_p=0.5, n=4, stream=True, stop=" ", max_tokens=10, presence_penalty=1.5, frequency_penalty=1.5, seed=12345)
)

print(
    request_embed_model("test")
)

print(
    request_embed_model(["test"], dimensions=100, caching=True)
)

print(llm_statistics.get_price("USD"), "💵")
print(llm_statistics.get_price("CNY"), "💴")
print(llm_statistics.get_price("EUR"), "💶")