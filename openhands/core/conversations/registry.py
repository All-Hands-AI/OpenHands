from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

BASE_DIR = Path.home() / '.openhands' / 'conversations'
META_PATH = Path.home() / '.openhands' / 'metadata.json'
LEGACY_DIRS = {
    'cli': Path.home() / '.openhands' / 'cli',
    'gui': Path.home() / '.openhands' / 'gui',
}

_migration_attempted = False


def ensure_paths() -> None:
    """Ensure the shared registry paths exist and perform legacy migration once."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not META_PATH.exists():
        _atomic_write(META_PATH, '[]')
    _maybe_migrate_legacy_content()


def list_conversations() -> list[dict[str, Any]]:
    """Return metadata for all stored conversations."""
    ensure_paths()
    metadata = _read_metadata()
    return _sort_metadata(metadata)


def add_conversation(conv_id: str, origin: str, title: str | None = None) -> None:
    """Register or update a conversation with its metadata."""
    ensure_paths()
    metadata = _read_metadata()

    timestamp = datetime.datetime.now().isoformat()
    entry = {
        'id': conv_id,
        'origin': origin,
        'title': title or f'{origin.upper()} Session',
        'timestamp': timestamp,
    }

    updated: list[dict[str, Any]] = [
        item for item in metadata if item.get('id') != conv_id
    ]
    updated.append(entry)

    _write_metadata(updated)


def get_conversation_path(conv_id: str) -> Path:
    """Return full path to the JSON file for this conversation."""
    ensure_paths()
    return BASE_DIR / f'{conv_id}.json'


def write_conversation_stub(conv_id: str, updates: dict[str, Any]) -> None:
    """Merge the provided updates into the stored conversation stub."""
    ensure_paths()
    path = get_conversation_path(conv_id)
    try:
        current = json.loads(path.read_text())
    except Exception:
        current = {}
    if not isinstance(current, dict):
        current = {}
    current.setdefault('id', conv_id)
    if 'origin' not in current and 'origin' in updates:
        current['origin'] = updates['origin']
    current.update(updates)
    _atomic_write(path, json.dumps(current, indent=2))


def _read_metadata() -> list[dict[str, Any]]:
    try:
        raw = META_PATH.read_text()
    except FileNotFoundError:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict) and item.get('id')]


def _write_metadata(metadata: list[dict[str, Any]]) -> None:
    serializable = _sort_metadata(metadata)
    _atomic_write(META_PATH, json.dumps(serializable, indent=2))


def _sort_metadata(metadata: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> datetime.datetime:
        timestamp = item.get('timestamp')
        if not isinstance(timestamp, str):
            return datetime.datetime.min
        try:
            return datetime.datetime.fromisoformat(timestamp)
        except ValueError:
            return datetime.datetime.min

    return sorted(metadata, key=sort_key, reverse=True)


def _atomic_write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode('utf-8') if isinstance(content, str) else content
    tmp_dir = str(path.parent)
    with NamedTemporaryFile(mode='wb', delete=False, dir=tmp_dir) as tmp_file:
        tmp_file.write(data)
        temp_path = Path(tmp_file.name)
    os.replace(temp_path, path)


def _maybe_migrate_legacy_content() -> None:
    global _migration_attempted
    if _migration_attempted:
        return
    _migration_attempted = True

    metadata = _read_metadata()
    seen_ids = {item.get('id') for item in metadata}
    metadata_changed = False

    for origin, legacy_dir in LEGACY_DIRS.items():
        if not legacy_dir.exists() or not legacy_dir.is_dir():
            continue
        for legacy_file in sorted(legacy_dir.glob('*.json')):
            conv_id = legacy_file.stem
            if not conv_id:
                continue
            destination = BASE_DIR / f'{conv_id}.json'
            if not destination.exists():
                try:
                    content = legacy_file.read_bytes()
                    _atomic_write(destination, content)
                except Exception:
                    continue
            if conv_id in seen_ids:
                continue
            timestamp = _resolve_timestamp(legacy_file)
            title = _resolve_title(legacy_file, origin)
            metadata.append(
                {
                    'id': conv_id,
                    'origin': origin,
                    'title': title,
                    'timestamp': timestamp,
                }
            )
            seen_ids.add(conv_id)
            metadata_changed = True

    if metadata_changed:
        _write_metadata(metadata)


def _resolve_title(source: Path, origin: str) -> str:
    try:
        data = json.loads(source.read_text())
    except Exception:
        data = {}
    title = data.get('title')
    if isinstance(title, str) and title.strip():
        return title
    return f'{origin.upper()} Session'


def _resolve_timestamp(source: Path) -> str:
    try:
        data = json.loads(source.read_text())
        ts = data.get('timestamp')
        if isinstance(ts, str) and ts.strip():
            return ts
    except Exception:
        pass
    try:
        stat = source.stat()
        return datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
    except Exception:
        return datetime.datetime.now().isoformat()
