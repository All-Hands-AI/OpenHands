import json
from typing import Any

from openhands.events.event import Event
from openhands.llm.metrics import Metrics, TokenUsage


def get_token_usage_for_event(event: Event, metrics: Metrics) -> TokenUsage | None:
    """
    Returns at most one token usage record for either:
      - `tool_call_metadata.model_response.id`, if possible
      - otherwise event.response_id, if set

    If neither exist or none matches in metrics.token_usages, returns None.
    """
    # 1) Use the tool_call_metadata's response.id if present
    if event.tool_call_metadata and event.tool_call_metadata.model_response:
        tool_response_id = event.tool_call_metadata.model_response.get('id')
        if tool_response_id:
            usage_rec = next(
                (u for u in metrics.token_usages if u.response_id == tool_response_id),
                None,
            )
            if usage_rec is not None:
                return usage_rec

    # 2) Fallback to the top-level event.response_id if present
    if event.response_id:
        return next(
            (u for u in metrics.token_usages if u.response_id == event.response_id),
            None,
        )

    return None


def get_token_usage_for_event_id(
    events: list[Event], event_id: int, metrics: Metrics
) -> TokenUsage | None:
    """
    Starting from the event with .id == event_id and moving backwards in `events`,
    find the first TokenUsage record (if any) associated either with:
      - tool_call_metadata.model_response.id, or
      - event.response_id
    Returns the first match found, or None if none is found.
    """
    # Find the index of the event with the given id
    idx = next((i for i, e in enumerate(events) if e.id == event_id), None)
    if idx is None:
        return None

    # Search backward from idx down to 0
    for i in range(idx, -1, -1):
        usage = get_token_usage_for_event(events[i], metrics)
        if usage is not None:
            return usage
    return None


def _extract_content_from_item(item: dict[str, Any]) -> dict[str, Any]:
    # Extract only relevant content fields
    extracted = item.copy()
    del extracted['chunkId']
    del extracted['documentId']
    return extracted


def process_knowledge_base(knowledge_base: dict[str, Any]) -> str:
    knowledge_content = []

    # Handle x_results (tweets/social media content)
    if 'x_results' in knowledge_base and len(knowledge_base['x_results']) > 0:
        x_results = [
            knowledge_base['x_results'][k] for k in knowledge_base['x_results']
        ]
        if x_results:
            extracted_x_results = [
                _extract_content_from_item(item) for item in x_results
            ]
            knowledge_content.append(f"""<XResult>
Description: Here are the tweets/social media posts related to the task, considered as knowledge base.
{json.dumps(extracted_x_results, ensure_ascii=False, indent=2)}
</XResult>""")

    # Handle knowledge_base_results
    if (
        'knowledge_base_results' in knowledge_base
        and len(knowledge_base['knowledge_base_results']) > 0
    ):
        kb_results = [
            knowledge_base['knowledge_base_results'][k]
            for k in knowledge_base['knowledge_base_results']
        ]
        if kb_results:
            extracted_kb_results = [
                _extract_content_from_item(item) for item in kb_results
            ]
            knowledge_content.append(f"""<KnowledgeBase>
{json.dumps(extracted_kb_results, ensure_ascii=False, indent=2)}
</KnowledgeBase>""")

    return chr(10).join(knowledge_content)
