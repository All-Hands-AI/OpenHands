import claude as Claude
import os


# https://github.com/jtsang4/claude-to-chatgpt/blob/main/claude_to_chatgpt/adapter.py
def convert_messages_to_prompt(messages, claude_role):
    prompt = ""
    for message in messages:
        role = message["role"]
        content = message["content"]
        prompt += f"\n\n{role}: {content}"
    prompt += f"\n\n{claude_role}: "
    return prompt


# DO NOT INVOKE DIRECTLY
class claude:

    client = Claude.Client(os.environ.get('access_key'))

    @staticmethod
    def request_model(msg, role, temperature, top_p, penalty_score):

        prompt = convert_messages_to_prompt(msg, role)

        response = claude.client.create(
            prompt = prompt,
            model = os.environ.get('model'),
            temperature=temperature,
            top_p=top_p,
            penalty_score=penalty_score
        )

        return response.text

    
    @staticmethod
    def request_submodel(msg, role, temperature, top_p, penalty_score):

        prompt = convert_messages_to_prompt(msg, role)

        response = claude.client.create(
            prompt = prompt,
            model = os.environ.get('submodel'),
            temperature=temperature,
            top_p=top_p,
            penalty_score=penalty_score
        )

        return response.text


    @staticmethod
    def request_embed_model(text: str):
        vector = claude.client.embed(
            input = text,
            model=os.environ.get('embed_model'),
        )

        return vector