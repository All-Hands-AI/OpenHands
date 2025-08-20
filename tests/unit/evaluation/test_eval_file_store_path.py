import os
from pathlib import Path

from evaluation.utils.shared import get_default_openhands_config_for_eval
from openhands.core.config.openhands_config import OpenHandsConfig


def test_eval_file_store_defaults_to_repo_local(tmp_path, monkeypatch):
    monkeypatch.delenv('EVAL_FILE_STORE_PATH', raising=False)
    monkeypatch.delenv('EVAL_SESSIONS_DIR', raising=False)
    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        cfg = OpenHandsConfig()
        cfg = get_default_openhands_config_for_eval(cfg)
        assert Path(cfg.file_store_path) == (tmp_path / '.eval_sessions').resolve()
        assert cfg.file_store == 'local'
    finally:
        os.chdir(prev_cwd)


def test_eval_file_store_env_override(monkeypatch):
    target = str((Path.cwd() / 'custom_eval_store').resolve())
    monkeypatch.setenv('EVAL_FILE_STORE_PATH', target)
    cfg = OpenHandsConfig()
    cfg = get_default_openhands_config_for_eval(cfg)
    assert cfg.file_store_path == target
    assert cfg.file_store == 'local'

    monkeypatch.delenv('EVAL_FILE_STORE_PATH', raising=False)
    target2 = str((Path.cwd() / 'another_store').resolve())
    monkeypatch.setenv('EVAL_SESSIONS_DIR', target2)
    cfg2 = OpenHandsConfig()
    cfg2 = get_default_openhands_config_for_eval(cfg2)
    assert cfg2.file_store_path == target2
    assert cfg2.file_store == 'local'
