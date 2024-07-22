# from opendevin.core.logger import opendevin_logger as logger
# from opendevin.llm.llm import LLM
# from opendevin.llm.messages import Message

# # from opendevin.events.action import AgentSummarizeAction
# from .prompts import (
#     MESSAGE_SUMMARY_WARNING_FRAC,
#     SUMMARY_PROMPT_SYSTEM,
#     parse_summary_response,
# )


# class MemoryCondenser:
#     def __init__(self, llm: LLM):
#         self.llm = llm

#     def condense(
#         self,
#         messages: list[Message],
#         state: State,
#     ):
#         # Start past the system message, and example messages.,
#         # and collect messages for summarization until we reach the desired truncation token fraction (eg 50%)
#         # Do not allow truncation  for in-context examples of function calling
#         history: ShortTermHistory = state.history
#         messages = self._get_messages(state=state)
#         token_counts = [self.llm.get_token_count([message]) for message in messages]
#         message_buffer_token_count = sum(
#             token_counts[2:]
#         )  # no system and example message

#         desired_token_count_to_summarize = int(
#             message_buffer_token_count
#             * self.llm.config.message_summary_trunc_tokens_frac
#         )

#         candidate_messages_to_summarize = []
#         tokens_so_far = 0
#         for event in history.get_events():
#             if event.id >= history.last_summarized_event_id:
#                 if isinstance(event, AgentSummarizeAction):
#                     action_message = self.get_action_message(event)
#                     if action_message:
#                         candidate_messages_to_summarize.append(action_message)
#                         tokens_so_far += self.llm.get_token_count([action_message])
#                 else:
#                     if isinstance(event, Action):
#                         message = self.get_action_message(event)
#                     elif isinstance(event, Observation):
#                         message = self.get_observation_message(event)
#                     else:
#                         raise ValueError(f'Unknown event type: {type(event)}')
#                     if message:
#                         candidate_messages_to_summarize.append(message)
#                         tokens_so_far += self.llm.get_token_count([message])
#             if tokens_so_far > desired_token_count_to_summarize:
#                 last_summarized_event_id = event.id
#                 break

#         # TODO: Add functionality for preserving last N messages
#         # MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST = 3
#         # if preserve_last_N_messages:
#         #     candidate_messages_to_summarize = candidate_messages_to_summarize[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]
#         #     token_counts = token_counts[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]

#         print(
#             f'message_summary_trunc_tokens_frac={self.llm.config.message_summary_trunc_tokens_frac}'
#         )
#         # print(f'MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST={MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST}')
#         print(f'token_counts={token_counts}')
#         print(f'message_buffer_token_count={message_buffer_token_count}')
#         print(f'desired_token_count_to_summarize={desired_token_count_to_summarize}')
#         print(
#             f'len(candidate_messages_to_summarize)={len(candidate_messages_to_summarize)}'
#         )

#         if len(candidate_messages_to_summarize) == 0:
#             raise SummarizeError(
#                 f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(messages)}]"
#             )

#         # TODO: Try to make an assistant message come after the cutoff

#         message_sequence_to_summarize = candidate_messages_to_summarize

#         if len(message_sequence_to_summarize) <= 1:
#             # This prevents a potential infinite loop of summarizing the same message over and over
#             raise SummarizeError(
#                 f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(message_sequence_to_summarize)} <= 1]"
#             )
#         else:
#             print(
#                 f'Attempting to summarize with last summarized event id = {last_summarized_event_id}'
#             )

#         summary_action: AgentSummarizeAction = self.memory_condenser.summarize_messages(
#             message_sequence_to_summarize=message_sequence_to_summarize
#         )
#         summary_action.last_summarized_event_id = last_summarized_event_id
#         print(f'Got summary: {summary_action}')
#         history.add_summary(summary_action)
#         print('Added summary to history')


#     def _format_summary_history(self, message_history: list[dict]) -> str:
#         # TODO use existing prompt formatters for this (eg ChatML)
#         return '\n'.join([f'{m["role"]}: {m["content"]}' for m in message_history])

#     def summarize_messages(self, message_sequence_to_summarize: list[Message]):
#         """Summarize a message sequence using LLM"""
#         context_window = self.llm.config.max_input_tokens
#         summary_prompt = SUMMARY_PROMPT_SYSTEM
#         summary_input = self._format_summary_history(
#             self.llm.get_text_messages(message_sequence_to_summarize)
#         )
#         summary_input_tkns = self.llm.get_token_count(summary_input)
#         if context_window is None:
#             raise ValueError('context_window should not be None')
#         if summary_input_tkns > MESSAGE_SUMMARY_WARNING_FRAC * context_window:
#             trunc_ratio = (
#                 MESSAGE_SUMMARY_WARNING_FRAC * context_window / summary_input_tkns
#             ) * 0.8  # For good measure...
#             cutoff = int(len(message_sequence_to_summarize) * trunc_ratio)
#             summary_input = str(
#                 [
#                     self.summarize_messages(
#                         message_sequence_to_summarize=message_sequence_to_summarize[
#                             :cutoff
#                         ]
#                     )
#                 ]
#                 + message_sequence_to_summarize[cutoff:]
#             )

#         message_sequence = []
#         message_sequence.append({'role': 'system', 'content': summary_prompt})

#         # TODO: Check if this feature is needed
#         # if insert_acknowledgement_assistant_message:
#         #     message_sequence.append(Message(user_id=dummy_user_id, agent_id=dummy_agent_id, role="assistant", text=MESSAGE_SUMMARY_REQUEST_ACK))

#         message_sequence.append({'role': 'user', 'content': summary_input})

#         response = self.llm.completion(
#             messages=message_sequence,
#             stop=[
#                 '</execute_ipython>',
#                 '</execute_bash>',
#                 '</execute_browse>',
#             ],
#             temperature=0.0,
#         )

#         print(f'summarize_messages gpt reply: {response.choices[0]}')

#         action_response = response['choices'][0]['message']['content']
#         action = parse_summary_response(action_response)
#         return action
