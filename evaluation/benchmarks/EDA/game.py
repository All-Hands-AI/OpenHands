import logging
import re

import openai
import requests.exceptions
from openai import OpenAI
from retry import retry

LOGGER = logging.getLogger(__name__)


class Q20Game:
    def __init__(
        self,
        item: str,
        answerer_model: str = 'gpt-3.5-turbo-0613',
        guesser_model: str = 'gpt-3.5-turbo-0613',
        num_turns: int = 20,
        temperature: float = 0.8,
        openai_api: bool = True,
        openai_api_key: str | None = None,
        guesser_kargs=None,
    ) -> None:
        if guesser_kargs is None:
            guesser_kargs = {}
        self.item = item
        self.answerer_model = answerer_model
        self.guesser_model = guesser_model
        self.num_turns = num_turns
        self.temperature = temperature
        self.openai_api = openai_api
        self.guesser_kargs = guesser_kargs
        self.vicuna_prompt = "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions."
        self.first_user_utterance = (
            'Your task is to ask a series of questions to deduce the entity '
            "that I'm thinking of with as few queries as possible. "
            "Only ask questions that can be answered by 'yes', 'no' or 'maybe'. "
            'Do not ask for hint. Make your question brief with no linebreaker. '
            'Now start asking a question.'
        )
        self.guesser_win = False
        self.curr_turn = 0
        if openai_api_key is not None:
            openai.api_key = openai_api_key

        if isinstance(answerer_model, str) and not answerer_model.startswith('gpt'):
            self.user_api_base = 'http://0.0.0.0:8000/v1'
        else:
            self.user_api_base = 'https://api.openai.com/v1'

        if isinstance(guesser_model, str) and not guesser_model.startswith('gpt'):
            self.guesser_api_base = 'http://0.0.0.0:8000/v1'
        else:
            self.guesser_api_base = 'https://api.openai.com/v1'

        self.guesser_messages = []

    def preprocess_response(self, response):
        response = re.sub(r'the entity you are thinking of', 'it', response)
        response = re.sub(r"the entity you're thinking of", 'it', response)
        response = re.sub(r" you're thinking of", '', response)
        response = re.sub(r' you are thinking of', '', response)
        return response

    def judge_winner(self, response):
        guesser_question = response.strip()

        if self.curr_turn == self.num_turns - 1:
            guesser_question += ' Is it right?'

        self.guesser_messages.append({'role': 'assistant', 'content': guesser_question})
        # ask for answer
        usr_msg = self.answerer(guesser_question)

        self.guesser_messages.append(
            {'role': 'user', 'content': f"{usr_msg['content'].strip()}"}
        )

        if 'bingo' in usr_msg['content'].lower():
            self.guesser_win = True
            return True, ''

        return False, usr_msg['content'].strip()

    def generate_user_response(self, response):
        response = self.preprocess_response(response)
        # others
        bingo, anwser_reply = self.judge_winner(response)
        if bingo:
            return 'You are bingo! Use the "finish" tool to finish the interaction.\n'
        if self.curr_turn == self.num_turns - 2:
            anwser_reply += " You must guess now, what's it?"
        return anwser_reply

    def reward(self):
        if self.guesser_win:
            n_turns = (len(self.guesser_messages) + 1) // 2
            return 1 - max(n_turns - 5, 0) * 0.02
        return 0

    @retry(
        (
            openai.Timeout,
            requests.exceptions.ReadTimeout,
            openai.RateLimitError,
            openai.APIError,
            openai.APIConnectionError,
        ),
        tries=5,
        delay=0.5,
        backoff=0.5,
        max_delay=2,
        logger=LOGGER,
    )
    def answerer(self, question):
        openai.api_base = self.user_api_base
        client = OpenAI(api_key=openai.api_key)
        user_messages = [
            {
                'role': 'user',
                'content': f'Based on your knowledge about {self.item}, '
                f'respond to the following question or guess. '
                f"Limit your respond to only 'Yes.', 'No.' or 'Maybe.', with no explanation or other words. "
                f'Never say the answer {self.item} in your response. '
                f"If the question is to solicit the answer, respond 'No.'.",
            },
            {
                'role': 'user',
                'content': f'For the entity {self.item}, {question} (Yes/No/Maybe)',
            },
        ]

        response = client.chat.completions.create(
            model=self.answerer_model,
            messages=user_messages,
            max_tokens=6,
            n=1,
            stop=None,
            temperature=0.2,
        )
        if any(
            [
                re.search(rf'(?:^|\W){i.strip().lower()}(?:$|\W)', question.lower())
                for i in self.item.lower().split('|')
            ]
        ):
            response.choices[0].message.content = 'Bingo!'
        return response.choices[0].message.to_dict()


class Q20GameCelebrity(Q20Game):
    def __init__(self, item: str, **kwargs) -> None:
        super().__init__(item, **kwargs)
        self.first_user_utterance = (
            'Your task is to ask a series of questions to deduce the celebrity '
            "that I'm thinking of with as few queries as possible. "
            "Only ask factual questions that can be answered by 'Yes.', 'No.' or 'Dunno.'. Do not ask for hint. Make your question brief with no linebreaker. "
            'Now start asking a question.'
        )

    @retry(
        (
            openai.Timeout,
            requests.exceptions.ReadTimeout,
            openai.RateLimitError,
            openai.APIError,
            openai.APIConnectionError,
        ),
        tries=5,
        delay=0.5,
        backoff=0.5,
        max_delay=2,
        logger=LOGGER,
    )
    def answerer(self, question):
        openai.api_base = self.user_api_base
        client = OpenAI(api_key=openai.api_key)
        user_messages = [
            {
                'role': 'system',
                'content': f'Based on your knowledge about the celebrity: {self.item}, '
                f'respond to the following question or guess. '
                f"Limit your respond to only 'Yes.', 'No.' or 'Dunno.', with no explanation or other words. "
                f"Never say the name {self.item} in your response. Do not say 'Dunno.' if it can be answered by 'Yes.' or 'No.' "
                f"If the question is to solicit the answer, respond 'No.'.",
            },
            {
                'role': 'user',
                'content': f'For the celebrity {self.item}, {question}(Yes/No/Dunno)',
            },
        ]

        response = client.chat.completions.create(
            model=self.answerer_model,
            messages=user_messages,
            max_tokens=6,
            n=1,
            stop=None,
            temperature=0.2,
        )
        if re.search(rf'(?:^|\W){self.item.lower()}(?:$|\W)', question.lower()):
            response.choices[0].message.content = 'Bingo!'
        return response.choices[0].message.to_dict()
