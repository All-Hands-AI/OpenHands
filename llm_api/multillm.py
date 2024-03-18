from typing import List, Optional
import os
from llm_api.llm_api import llm_api
from langchain.llms.base import LLM
from litellm.utils import ModelResponse


class ChatMultiLLM(LLM):

    def __init__(self, temperature=None, top_p=None, presence_penalty=None, frequency_penalty=None, max_tokens=None):
        super().__init__()
        self.__temperature = temperature
        self.__top_p = top_p
        self.__presence_penalty = presence_penalty
        self.__frequency_penalty = frequency_penalty
        #self.__n = n
        self.__max_tokens = max_tokens
        #self.__stream = stream
        
    @property
    def _llm_type(self) -> str:
        return os.environ.get('model')

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:

        response = llm_api.request_model(
            messages=[{"role": "user", "content": prompt}],
            temperature=self.__temperature,
            top_p=self.__top_p,
            #n=self.__n,
            #stream=self.__stream,
            stop=stop,
            max_tokens=self.__max_tokens,
            presence_penalty=self.__presence_penalty,
            frequency_penalty=self.__frequency_penalty,
        )

        response:ModelResponse = response[0]
        return response.choices[0].message.get("content", "default")


'''
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

def get_chain(template):
    llm = ChatMultiLLM()
    prompt = PromptTemplate.from_template(template)
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    return llm_chain
'''