from __future__ import annotations

import os

from .types import SDKEvent


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def append_event_jsonl(jsonl_path: str, event: SDKEvent) -> None:
    _ensure_dir(jsonl_path)
    with open(jsonl_path, 'a', encoding='utf-8') as f:
        f.write(event.model_dump_json() + '\n')


def read_events_jsonl(jsonl_path: str) -> list[SDKEvent]:
    if not os.path.exists(jsonl_path):
        return []
    events: list[SDKEvent] = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(SDKEvent.model_validate_json(line))
    return events
