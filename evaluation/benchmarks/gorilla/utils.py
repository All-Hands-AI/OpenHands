import json
import os
from functools import partial

import httpx
import pandas as pd
from ast_eval_hf import ast_eval_hf, ast_parse
from ast_eval_tf import ast_eval_tf
from ast_eval_th import ast_eval_th


# This function is modified from Gorilla's APIBench implementations (https://github.com/ShishirPatil/gorilla/blob/main/eval/get_llm_responses.py).
def encode_question(question, api_name):
    """Encode multiple prompt instructions into a single string."""
    prompts = []
    if api_name == 'torch':
        api_name = 'torchhub'
        domains = '1. $DOMAIN is inferred from the task description and should include one of {Classification, Semantic Segmentation, Object Detection, Audio Separation, Video Classification, Text-to-Speech}.'
    elif api_name == 'hf':
        api_name = 'huggingface'
        domains = '1. $DOMAIN should include one of {Multimodal Feature Extraction, Multimodal Text-to-Image, Multimodal Image-to-Text, Multimodal Text-to-Video, \
        Multimodal Visual Question Answering, Multimodal Document Question Answer, Multimodal Graph Machine Learning, Computer Vision Depth Estimation,\
        Computer Vision Image Classification, Computer Vision Object Detection, Computer Vision Image Segmentation, Computer Vision Image-to-Image, \
        Computer Vision Unconditional Image Generation, Computer Vision Video Classification, Computer Vision Zero-Shor Image Classification, \
        Natural Language Processing Text Classification, Natural Language Processing Token Classification, Natural Language Processing Table Question Answering, \
        Natural Language Processing Question Answering, Natural Language Processing Zero-Shot Classification, Natural Language Processing Translation, \
        Natural Language Processing Summarization, Natural Language Processing Conversational, Natural Language Processing Text Generation, Natural Language Processing Fill-Mask,\
        Natural Language Processing Text2Text Generation, Natural Language Processing Sentence Similarity, Audio Text-to-Speech, Audio Automatic Speech Recognition, \
        Audio Audio-to-Audio, Audio Audio Classification, Audio Voice Activity Detection, Tabular Tabular Classification, Tabular Tabular Regression, \
        Reinforcement Learning Reinforcement Learning, Reinforcement Learning Robotics }'
    elif api_name == 'tf':
        api_name = 'tensorhub'
        domains = '1. $DOMAIN is inferred from the task description and should include one of {text-sequence-alignment, text-embedding, text-language-model, text-preprocessing, text-classification, text-generation, text-question-answering, text-retrieval-question-answering, text-segmentation, text-to-mel, image-classification, image-feature-vector, image-object-detection, image-segmentation, image-generator, image-pose-detection, image-rnn-agent, image-augmentation, image-classifier, image-style-transfer, image-aesthetic-quality, image-depth-estimation, image-super-resolution, image-deblurring, image-extrapolation, image-text-recognition, image-dehazing, image-deraining, image-enhancemenmt, image-classification-logits, image-frame-interpolation, image-text-detection, image-denoising, image-others, video-classification, video-feature-extraction, video-generation, video-audio-text, video-text, audio-embedding, audio-event-classification, audio-command-detection, audio-paralinguists-classification, audio-speech-to-text, audio-speech-synthesis, audio-synthesis, audio-pitch-extraction}'
    else:
        print('Error: API name is not supported.')

    prompt = (
        question
        + '\nWrite a python program in 1 to 2 lines to call API in '
        + api_name
        + '.\n\nThe answer should follow the format: <<<domain>>> $DOMAIN, <<<api_call>>>: $API_CALL, <<<api_provider>>>: $API_PROVIDER, <<<explanation>>>: $EXPLANATION, <<<code>>>: $CODE}. Here are the requirements:\n'
        + domains
        + '\n2. The $API_CALL should have only 1 line of code that calls api.\n3. The $API_PROVIDER should be the programming framework used.\n4. $EXPLANATION should be a step-by-step explanation.\n5. The $CODE is the python code.\n6. Do not repeat the format in your answer.'
    )
    # prompts.append({"role": "system", "content": ""})
    prompts = (
        'You are a helpful API writer who can write APIs based on requirements.\n'
        + prompt
    )
    return prompts


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def fetch_data(url, filename):
    cache_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return f.read()
    else:
        response = httpx.get(url)
        if response.status_code == 200:
            with open(cache_path, 'w') as f:
                f.write(response.text)
            return response.text
        else:
            raise Exception(f'Failed to fetch data from {url}')


def get_data_for_hub(hub: str):
    if hub == 'hf':
        question_data = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/eval/eval-data/questions/huggingface/questions_huggingface_0_shot.jsonl'
        api_dataset = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/data/api/huggingface_api.jsonl'
        apibench = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/data/apibench/huggingface_eval.json'
        ast_eval = ast_eval_hf
    elif hub == 'torch':
        question_data = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/eval/eval-data/questions/torchhub/questions_torchhub_0_shot.jsonl'
        api_dataset = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/data/api/torchhub_api.jsonl'
        apibench = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/data/apibench/torchhub_eval.json'
        ast_eval = ast_eval_th
    elif hub == 'tf':
        question_data = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/eval/eval-data/questions/tensorflowhub/questions_tensorflowhub_0_shot.jsonl'
        api_dataset = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/data/api/tensorflowhub_api.jsonl'
        apibench = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/refs/tags/v1.2/data/apibench/tensorflow_eval.json'
        ast_eval = ast_eval_tf

    question_data = fetch_data(question_data, 'question_data.jsonl')
    api_dataset = fetch_data(api_dataset, 'api_dataset.jsonl')
    apibench = fetch_data(apibench, 'apibench.json')

    # Parse question data
    questions = []
    question_ids = []
    for line in question_data.splitlines():
        data = json.loads(line)
        questions.append(data['text'])
        question_ids.append(data['question_id'])

    # Parse API dataset
    api_database = [json.loads(line) for line in api_dataset.splitlines()]

    # Parse question-answer pairs
    qa_pairs = [json.loads(line)['api_data'] for line in apibench.splitlines()]

    # Parse all apis to ast trees
    ast_database = []
    for data in api_database:
        ast_tree = ast_parse(data['api_call'])
        ast_database.append(ast_tree)
    ast_eval = partial(ast_eval, api_database, qa_pairs, ast_database)

    return pd.DataFrame(
        {
            'question_id': question_ids,
            'question': questions,
            'api_database': [api_database] * len(questions),
            'qa_pairs': [qa_pairs] * len(questions),
            'ast_database': [ast_database] * len(questions),
            'ast_eval': [ast_eval] * len(questions),
            'hub': [hub] * len(questions),
        }
    )
