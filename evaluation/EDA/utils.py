import logging
from typing import Dict, List

import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

LOGGER = logging.getLogger(__name__)

avatars: Dict[str, str] = {
    'user': '🤖',
    'assistant': '🧑‍💻',
}


def display_dialog(message_history: List[Dict[str, str]]) -> None:
    """Streamlit-chat message function does not persist once streamlit reloads
    UI as far as I can tell. We need to render the whole dialog.

    Parameters
    ----------
    message_history :   List of messages in the form of
                        [
                            {
                                "role": "user",
                                "content": f"Your task is to ask a series of questions to deduce the entity "
                                f"that I'm thinking of with as few queries as possible. "
                                f"Only ask questions that can be answered by 'yes', 'no' or 'maybe'. "
                                f"Now start asking a question.",
                            }
                        ]

    Returns
    -------
    """
    for i in range(len(message_history)):
        with st.chat_message(
            message_history[i]['role'], avatar=avatars[message_history[i]['role']]
        ):
            st.write(f"{message_history[i]['content']}")
        if i == len(message_history) - 2:
            with st.expander("ChatGPT would've asked"):
                with st.chat_message(
                    message_history[i]['role'],
                    avatar='🦾',
                ):
                    st.write(st.session_state['alternative_question'])


def boolean_string(s):
    if s.lower() not in {'false', 'true'}:
        raise ValueError('Not a valid boolean string')
    return s.lower() == 'true'


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
