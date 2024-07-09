from opendevin.core.logger import opendevin_logger as logger
from opendevin.llm.llm import LLM

from .prompts import MESSAGE_SUMMARY_WARNING_FRAC, SUMMARY_PROMPT_SYSTEM


class MemoryCondenser:
    def condense(self, summarize_prompt: str, llm: LLM):
        """
        Attempts to condense the monologue by using the llm

        Parameters:
        - llm (LLM): llm to be used for summarization

        Raises:
        - Exception: the same exception as it got from the llm or processing the response
        """

        try:
            messages = [{'content': summarize_prompt, 'role': 'user'}]
            resp = llm.completion(messages=messages)
            summary_response = resp['choices'][0]['message']['content']
            return summary_response
        except Exception as e:
            logger.error('Error condensing thoughts: %s', str(e), exc_info=False)

            # TODO If the llm fails with ContextWindowExceededError, we can try to condense the monologue chunk by chunk
            raise


def _format_summary_history(message_history: list[dict]):
    # TODO use existing prompt formatters for this (eg ChatML)
    return '\n'.join([f'{m["role"]}: {m["content"]}' for m in message_history])


def summarize_messages(message_sequence_to_summarize: list[dict], llm: LLM):
    """Summarize a message sequence using LLM"""
    context_window = llm.max_input_tokens
    summary_prompt = SUMMARY_PROMPT_SYSTEM
    summary_input = _format_summary_history(message_sequence_to_summarize)
    summary_input_tkns = llm.get_token_count(summary_input)

    if summary_input_tkns > MESSAGE_SUMMARY_WARNING_FRAC * context_window:
        trunc_ratio = (
            MESSAGE_SUMMARY_WARNING_FRAC * context_window / summary_input_tkns
        ) * 0.8  # For good measure...
        cutoff = int(len(message_sequence_to_summarize) * trunc_ratio)
        summary_input = str(
            [
                summarize_messages(
                    message_sequence_to_summarize=message_sequence_to_summarize[
                        :cutoff
                    ],
                    llm=llm,
                )
            ]
            + message_sequence_to_summarize[cutoff:]
        )

    # dummy_user_id = uuid.uuid4()
    # dummy_agent_id = uuid.uuid4()
    message_sequence = []
    message_sequence.append({'role': 'system', 'text': summary_prompt})

    # TODO: Check if this feature is needed
    # if insert_acknowledgement_assistant_message:
    #     message_sequence.append(Message(user_id=dummy_user_id, agent_id=dummy_agent_id, role="assistant", text=MESSAGE_SUMMARY_REQUEST_ACK))

    message_sequence.append({'role': 'user', 'text': summary_input})

    response = llm.completion(
        messages=message_sequence,
        stop=[
            '</execute_ipython>',
            '</execute_bash>',
            '</execute_browse>',
        ],
        temperature=0.0,
    )

    print(f'summarize_messages gpt reply: {response.choices[0]}')
    reply = response.choices[0].message.content
    return reply


# def summarize_messages(
#     agent_state: AgentState,
#     message_sequence_to_summarize: List[Message],
#     insert_acknowledgement_assistant_message: bool = True,
# ):
#     """Summarize a message sequence using GPT"""
#     # we need the context_window
#     context_window = agent_state.llm_config.context_window

#     summary_prompt = SUMMARY_PROMPT_SYSTEM
#     summary_input = _format_summary_history(message_sequence_to_summarize)
#     summary_input_tkns = count_tokens(summary_input)
#     if summary_input_tkns > MESSAGE_SUMMARY_WARNING_FRAC * context_window:
#         trunc_ratio = (MESSAGE_SUMMARY_WARNING_FRAC * context_window / summary_input_tkns) * 0.8  # For good measure...
#         cutoff = int(len(message_sequence_to_summarize) * trunc_ratio)
#         summary_input = str(
#             [summarize_messages(agent_state, message_sequence_to_summarize=message_sequence_to_summarize[:cutoff])]
#             + message_sequence_to_summarize[cutoff:]
#         )

#     dummy_user_id = uuid.uuid4()
#     dummy_agent_id = uuid.uuid4()
#     message_sequence = []
#     message_sequence.append(Message(user_id=dummy_user_id, agent_id=dummy_agent_id, role="system", text=summary_prompt))
#     if insert_acknowledgement_assistant_message:
#         message_sequence.append(Message(user_id=dummy_user_id, agent_id=dummy_agent_id, role="assistant", text=MESSAGE_SUMMARY_REQUEST_ACK))
#     message_sequence.append(Message(user_id=dummy_user_id, agent_id=dummy_agent_id, role="user", text=summary_input))

#     response = create(
#         llm_config=agent_state.llm_config,
#         user_id=agent_state.user_id,
#         messages=message_sequence,
#     )

#     printd(f"summarize_messages gpt reply: {response.choices[0]}")
#     reply = response.choices[0].message.content
#     return reply
