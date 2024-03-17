from litellm.utils import ModelResponse
from pyexchangelib import CurrencyExchange
import os


class llm_statistics:

    total_tokens = 0
    total_subtokens = 0
    total_embed_tokens = 0

    @staticmethod
    def use_token(response: ModelResponse):
        usage = response.usage
        if usage.total_tokens:
            llm_statistics.total_tokens += usage.total_tokens
        else:
            if usage.prompt_tokens:
                llm_statistics.total_tokens += usage.prompt_tokens
            if usage.completion_tokens:
                llm_statistics.total_tokens += usage.completion_tokens

    @staticmethod
    def use_subtoken(response: ModelResponse):
        usage = response.usage
        if usage.total_tokens:
            llm_statistics.total_subtokens += usage.total_tokens
        else:
            if usage.prompt_tokens:
                llm_statistics.total_subtokens += usage.prompt_tokens
            if usage.completion_tokens:
                llm_statistics.total_subtokens += usage.completion_tokens

    @staticmethod
    def use_embed_token(response: ModelResponse):
        usage = response.usage
        if usage.total_tokens:
            llm_statistics.total_embed_tokens += usage.total_tokens
        else:
            if usage.prompt_tokens:
                llm_statistics.total_embed_tokens += usage.prompt_tokens
            if usage.completion_tokens:
                llm_statistics.total_embed_tokens += usage.completion_tokens

    @staticmethod
    def get_price(currency="USD"):
        total = 0

        rate = CurrencyExchange.get_rate(os.environ.get('cost_currency'), currency)
        total += llm_statistics.total_tokens * float(os.environ.get('cost')) * rate

        rate = CurrencyExchange.get_rate(os.environ.get('subcost_currency'), currency)
        total += llm_statistics.total_subtokens * float(os.environ.get('subcost')) * rate

        rate = CurrencyExchange.get_rate(os.environ.get('cost_embed_currency'), currency)
        total += llm_statistics.total_embed_tokens * float(os.environ.get('embed_cost')) * rate

        return total