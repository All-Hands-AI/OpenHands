import json
from functools import partial

import requests
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


def get_data(hub):
    if hub == 'hf':
        question_data = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/eval/eval-data/questions/huggingface/questions_huggingface_0_shot.jsonl'
        api_dataset = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/data/api/huggingface_api.jsonl'
        apibench = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/data/apibench/huggingface_eval.json'
        ast_eval = ast_eval_hf
    if hub == 'torch':
        question_data = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/eval/eval-data/questions/torchhub/questions_torchhub_0_shot.jsonl'
        api_dataset = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/data/api/torchhub_api.jsonl'
        apibench = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/data/apibench/torchhub_eval.json'
        ast_eval = ast_eval_th
    if hub == 'tf':
        question_data = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/eval/eval-data/questions/tensorflowhub/questions_tensorflowhub_0_shot.jsonl'
        api_dataset = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/data/api/tensorflowhub_api.jsonl'
        apibench = 'https://raw.githubusercontent.com/ShishirPatil/gorilla/main/data/apibench/tensorflow_eval.json'
        ast_eval = ast_eval_tf

    # get questions and question_ids
    questions = []
    question_ids = []
    question_data = requests.get(question_data)
    if question_data.status_code == 200:
        lines = question_data.text.splitlines()
        for line in lines:
            questions.append(json.loads(line)['text'])
            question_ids.append(json.loads(line)['question_id'])

    # get the api datasest
    api_database = []
    api_dataset = requests.get(api_dataset)
    if api_dataset.status_code == 200:
        lines = api_dataset.text.splitlines()
        for line in lines:
            api_database.append(json.loads(line))

    # get the question answer pair datasest
    qa_pairs = []
    apibench = requests.get(apibench)
    if apibench.status_code == 200:
        lines = apibench.text.splitlines()
        for line in lines:
            qa_pairs.append(json.loads(line)['api_data'])

    # Parse all apis to ast trees
    ast_database = []
    for data in api_database:
        ast_tree = ast_parse(data['api_call'])
        ast_database.append(ast_tree)
    ast_eval = partial(ast_eval, api_database, qa_pairs, ast_database)
    return questions, question_ids, ast_eval
