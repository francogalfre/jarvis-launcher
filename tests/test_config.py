import json
import pytest
from pathlib import Path
from unittest.mock import patch
from jarvis_launcher import config


def test_load_creates_defaults_when_no_file(tmp_path):
    config_file = tmp_path / "config.json"
    with patch.object(config, "CONFIG_FILE", config_file), \
         patch.object(config, "CONFIG_DIR", tmp_path):
        result = config.load()
    assert result["sensitivity"] == 0.15
    assert result["required_claps"] == 2
    assert config_file.exists()


def test_load_reads_existing_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"sensitivity": 0.25, "required_claps": 3}))
    with patch.object(config, "CONFIG_FILE", config_file), \
         patch.object(config, "CONFIG_DIR", tmp_path):
        result = config.load()
    assert result["sensitivity"] == 0.25
    assert result["required_claps"] == 3
    assert result["open_claude_code"] is True


def test_load_merges_missing_keys_with_defaults(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"sensitivity": 0.10}))
    with patch.object(config, "CONFIG_FILE", config_file), \
         patch.object(config, "CONFIG_DIR", tmp_path):
        result = config.load()
    assert result["sensitivity"] == 0.10
    assert "voice" in result
    assert "youtube_url" in result
