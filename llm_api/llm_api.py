import os
import importlib

platform = os.environ.get('platform')

api_module = importlib.import_module(f"llm_api.{platform}")
api = getattr(api_module, platform)



'''
msg: the message to be fed into llm, with a structure as follows:
    [
        {
            "role": "user",
            "content": "hello"
        },
        {
            "role": "assistant",
            "content": "hello, how can i assist you today?"
        },
        ...
    ]
role: the role of ai in this round of chat, could be any value like 'CEO', 'Programmer', etc.
temperature:   float value, ranging between (0  , 1.0]
top_p:         float value, ranging between [0  , 1.0]
penalty_score: float value, ranging between [1.0, 2.0]

returns ->
    a single string, the response of llm
'''
def request_model(msg, role="assistant", temperature=0.8, top_p=0.8, penalty_score=1.0):
    return api.request_model(msg, role, temperature, top_p, penalty_score)


'''
the inputs and output are all the same to the `request_model` function above
'''
def request_submodel(msg, role="assistant", temperature=0.8, top_p=0.8, penalty_score=1.0):
    return api.request_submodel(msg, role, temperature, top_p, penalty_score)


'''
text: a single string, the text to be victorized

returns ->
    a list, containing float numbers, with undetermined length
'''
def request_embed_model(text):
    return api.request_embed_model(text)