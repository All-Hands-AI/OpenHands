import json
import logging
import os
import re
from typing import Optional

import openai
import requests.exceptions
import torch
from openai import OpenAI
from retry import retry
from transformers import AutoModelForCausalLM, AutoTokenizer

LOGGER = logging.getLogger(__name__)


def load_model(path):
    print('Loading model...')
    tokenizer = AutoTokenizer.from_pretrained(path, use_fast=False)
    print('Tokenizer loaded.')
    model = AutoModelForCausalLM.from_pretrained(
        path, low_cpu_mem_usage=True, torch_dtype=torch.float16
    ).cuda()
    print('Model loaded.')
    # model.half().cuda()
    return model, tokenizer


class Q20Game:
    def __init__(
        self,
        item: str,
        answerer_model: str = 'gpt-3.5-turbo-0613',
        guesser_model: str = 'gpt-3.5-turbo-0613',
        num_turns: int = 20,
        temperature: float = 0.8,
        openai_api: bool = True,
        openai_api_key: Optional[str] = None,
        guesser_kargs={},
    ) -> None:
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

    def confusion_matrix(self, path):
        self.reset()
        with open(path) as f:
            raw_messages = json.load(f)
            self.item = path.split('/')[-1].split('_')[0]
            roles = ['assistant', 'user']
            for i, message in enumerate(raw_messages):
                self.guesser_messages.append(
                    {'role': roles[i % 2], 'content': message['content']}
                )

        self.guesser_messages = self.guesser_messages[:-2]
        self.guesser_messages[-1]['content'] = (
            self.guesser_messages[-1]['content'] + " You must guess now, what's it?"
        )
        guesser_msg = self.guesser(self.guesser_messages)
        self.guesser_messages.append(guesser_msg)
        guesser_question = guesser_msg['content'].strip()
        self.guesser_messages[-1]['content'] = (
            self.guesser_messages[-1]['content'] + ' Is it right?'
        )
        usr_msg = self.answerer(guesser_question)
        self.guesser_messages.append(
            {'role': 'user', 'content': f"{usr_msg['content'].strip()}"}
        )

        if 'bingo' in self.guesser_messages[-1]['content'].lower():
            self.guesser_win = True
            return True

        return False

    @retry(
        (
            openai.Timeout,
            requests.exceptions.ReadTimeout,
            openai.RateLimitError,
            openai.APIError,
            requests.exceptions.HTTPError,
            openai.APIConnectionError,
        ),
        tries=5,
        delay=0.5,
        backoff=0.5,
        max_delay=2,
        logger=LOGGER,
    )
    def guesser(self, messages):
        if not self.guesser_model.startswith('gpt'):  # hf model
            self.guesser_model, self.guesser_tokenizer = load_model(self.guesser_model)

            # """Wraps hf's `generate` adding some specific method's defaults"""
            assert not self.openai_api
            prompt = self.dialog_history() + ' ASSISTANT:'
            input_ids = torch.tensor(
                [self.guesser_tokenizer.encode(prompt, add_special_tokens=True)]
            )  # TODO check if huggingface is using the same format.
            input_ids = input_ids.to(self.guesser_model.base_model.device)
            attention_mask = None

            with torch.no_grad():
                gen = self.guesser_model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    **self.guesser_kargs,
                )
                gen_str = (
                    self.guesser_tokenizer.decode(gen[0][input_ids[0].shape[0] :])
                    .split('</s>')[0]
                    .split('USER')[0]
                    .lstrip()
                    .strip()
                )

                return {
                    'role': 'assistant',
                    'content': gen_str,
                }
        else:
            openai.api_base = self.guesser_api_base
            client = OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model=self.guesser_model,
                messages=messages,
                max_tokens=64,
                n=1,
                stop=None,
                temperature=self.temperature,
            )
            return {
                'role': 'assistant',
                'content': response.choices[0].message.to_dict()['content'].strip(),
            }

    def dialog_history(self):
        history = self.vicuna_prompt + ' '
        for item in self.guesser_messages:
            if item['role'].upper() == 'USER':
                history += 'USER: ' + item['content']
            elif item['role'].upper() == 'ASSISTANT':
                history += ' ' + 'ASSISTANT: ' + item['content'] + '</s>'
        return history


    def preprocess_response(self,response):
        response = re.sub(
            r'the entity you are thinking of', 'it', response
        )
        response = re.sub(
            r"the entity you're thinking of", 'it', response
        )
        response = re.sub(
            r" you're thinking of", '', response
        )
        response = re.sub(
            r' you are thinking of', '', response
        )
        self.guesser_messages.append(response)
        return response

    def judge_winner(self, response):
        guesser_question = response.strip()

        if self.curr_turn == self.num_turns - 1:
            guesser_question += ' Is it right?'
        # ask for answer
        usr_msg = self.answerer(guesser_question)

        if 'bingo' in usr_msg['content'].lower():
            self.guesser_win = True
            return True, ""
        
        return False, usr_msg['content'].strip()
    
    def generate_user_response(self, response):
        response = self.preprocess_response(response)
        # others
        bingo, anwser_reply = self.judge_winner(response)
        if bingo:
            return "You are bingo! quit now, run: <execute_bash> exit </execute_bash>.\n"
        if self.curr_turn == self.num_turns - 2:
            anwser_reply += " You must guess now, what's it?"
        return anwser_reply

    def game_play(self, user_mode=False):
        self.reset()
        # print(f"Item: {self.item}")
        for t in range(self.num_turns):
            # System asking a question
            if (not user_mode) or user_mode is None:
                guesser_msg = self.guesser(self.guesser_messages)
                guesser_msg['content'] = re.sub(
                    r'the entity you are thinking of', 'it', guesser_msg['content']
                )
                guesser_msg['content'] = re.sub(
                    r"the entity you're thinking of", 'it', guesser_msg['content']
                )
                guesser_msg['content'] = re.sub(
                    r" you're thinking of", '', guesser_msg['content']
                )
                guesser_msg['content'] = re.sub(
                    r' you are thinking of', '', guesser_msg['content']
                )
            else:
                user_q = input(
                    f'Type in your questions for turn {t+1}. (e.g. Is it a living thing?)\n'
                )
                guesser_msg = {'role': 'assistant', 'content': user_q}
            self.guesser_messages.append(guesser_msg)
            guesser_question = guesser_msg['content'].strip()

            if t == self.num_turns - 1:
                self.guesser_messages[-1]['content'] = (
                    self.guesser_messages[-1]['content'] + ' Is it right?'
                )

            usr_msg = self.answerer(guesser_question)
            self.guesser_messages.append(
                {'role': 'user', 'content': f"{usr_msg['content'].strip()}"}
            )

            if 'bingo' in usr_msg['content'].lower():
                self.guesser_win = True
                return True

            if t == self.num_turns - 2:
                self.guesser_messages[-1]['content'] = (
                    self.guesser_messages[-1]['content']
                    + " You must guess now, what's it?"
                )

        return False

    def save_session(self, path):
        # Print the conversation
        if not os.path.exists(path):
            os.makedirs(path)
        output_file = os.path.join(path, f'{self.item}.txt')
        with open(output_file, 'w') as out_f:
            out_f.write(f'item: {self.item}\n')
            for t, message in enumerate(self.guesser_messages):
                out_f.write(
                    f"Turn {(t+1)//2}, {message['role'].capitalize()}: {message['content'].lstrip()}\n"
                )

    def reward(self):
        if self.guesser_win:
            n_turns = (len(self.guesser_messages) + 1) // 2
            return 1 - max(n_turns - 5, 0) * 0.02
        return 0

    def num_success(self):
        return 1 if self.guesser_win else 0

    def num_yes(self):
        n_yes = sum(
            ['yes' in msg['content'].lower() for msg in self.guesser_messages[2::2]]
        )
        return n_yes

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

    def reset(self):
        # Initialize the conversation
        self.curr_turn = 0
        self.guesser_messages = [
            {
                'role': 'user',
                'content': self.first_user_utterance,
            }
        ]


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
        user_messages = [
            {
                'role': 'system',
                'content': f'Based on on your knowledge about the celebrity: {self.item}, '
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

        response = openai.ChatCompletion.create(
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

    def reset(self):
        # Initialize the conversation
        self.guesser_messages = [
            {
                'role': 'user',
                'content': self.first_user_utterance,
            }
        ]
