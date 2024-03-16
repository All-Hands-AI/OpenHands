from llm_api.llm_api import request_model, request_submodel, request_embed_model

print(
    request_model(
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
    )
)

print(
    request_embed_model("test")
)