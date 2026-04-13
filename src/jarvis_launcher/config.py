import json
import subprocess
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".jarvis-launcher"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS: dict = {
    "sensitivity": 0.15,
    "noise_multiplier": 3.0,
    "required_claps": 2,
    "timeout_reset": 3.0,
    "min_seconds_between_claps": 0.3,
    "youtube_url": "https://www.youtube.com/watch?v=v2AC41dglnM",
    "open_claude_code": True,
    "open_cursor": True,
    "open_youtube": True,
    "voice": "en-GB-RyanNeural",
}


def load() -> dict:
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=2))
        return DEFAULTS.copy()
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    return {**DEFAULTS, **data}


def open_in_editor() -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(CONFIG_FILE)])
    elif sys.platform == "win32":
        subprocess.Popen(["start", str(CONFIG_FILE)], shell=True)
    else:
        subprocess.Popen(["xdg-open", str(CONFIG_FILE)])
