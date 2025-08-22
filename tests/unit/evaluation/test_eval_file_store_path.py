import os
from pathlib import Path

from evaluation.utils.shared import get_openhands_config_for_eval


def test_eval_file_store_defaults_to_repo_local(tmp_path, monkeypatch):
    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        cfg = get_openhands_config_for_eval()
        assert Path(cfg.file_store_path) == (tmp_path / '.eval_sessions').resolve()
        assert cfg.file_store == 'local'
    finally:
        os.chdir(prev_cwd)


def test_eval_file_store_is_hard_coded_repo_local(tmp_path):
    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        cfg = get_openhands_config_for_eval()
        assert Path(cfg.file_store_path) == (tmp_path / '.eval_sessions').resolve()
        assert cfg.file_store == 'local'
    finally:
        os.chdir(prev_cwd)
