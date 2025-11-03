import json
from datetime import datetime, timezone

import pytest

from openhands.core.conversations import registry


@pytest.fixture(autouse=True)
def reset_registry(monkeypatch):
    monkeypatch.setattr(registry, 'LEGACY_DIRS', {})
    registry._migration_attempted = False


def _configure_paths(tmp_path, monkeypatch):
    base_dir = tmp_path / 'conversations'
    meta_path = tmp_path / 'metadata.json'
    monkeypatch.setattr(registry, 'BASE_DIR', base_dir)
    monkeypatch.setattr(registry, 'META_PATH', meta_path)
    return base_dir, meta_path


def test_add_and_list_conversations(tmp_path, monkeypatch):
    _configure_paths(tmp_path, monkeypatch)

    registry.add_conversation('abc123', origin='cli', title='Test CLI')
    meta = registry.list_conversations()

    assert len(meta) == 1
    assert meta[0]['origin'] == 'cli'
    assert meta[0]['id'] == 'abc123'
    assert meta[0]['title'] == 'Test CLI'


def test_migrate_legacy_conversations(tmp_path, monkeypatch):
    base_dir, meta_path = _configure_paths(tmp_path, monkeypatch)
    legacy_cli = tmp_path / 'cli'
    legacy_cli.mkdir()
    legacy_file = legacy_cli / 'legacy-1.json'
    legacy_payload = {
        'title': 'Legacy CLI Session',
        'timestamp': datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
    }
    legacy_file.write_text(json.dumps(legacy_payload))

    monkeypatch.setattr(
        registry,
        'LEGACY_DIRS',
        {
            'cli': legacy_cli,
        },
    )
    registry._migration_attempted = False

    conversations = registry.list_conversations()
    assert len(conversations) == 1
    migrated = conversations[0]
    assert migrated['id'] == 'legacy-1'
    assert migrated['origin'] == 'cli'
    assert migrated['title'] == 'Legacy CLI Session'
    assert base_dir.joinpath('legacy-1.json').exists()


def test_write_conversation_stub_merges(tmp_path, monkeypatch):
    base_dir, _ = _configure_paths(tmp_path, monkeypatch)

    registry.write_conversation_stub(
        'merge-1', {'origin': 'cli', 'title': 'Initial', 'updated_at': '2024-01-01T00:00:00'}
    )
    registry.write_conversation_stub('merge-1', {'title': 'Updated'})

    payload = json.loads(base_dir.joinpath('merge-1.json').read_text())
    assert payload['id'] == 'merge-1'
    assert payload['origin'] == 'cli'
    assert payload['title'] == 'Updated'
