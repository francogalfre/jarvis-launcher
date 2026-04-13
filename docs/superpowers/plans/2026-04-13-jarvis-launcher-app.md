# jarvis-launcher Cross-Platform App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the single-file `src/applause_launcher.py` into a cross-platform pip package and standalone binary: a background daemon with a system tray icon that detects two claps and launches configured apps on Linux, macOS, and Windows.

**Architecture:** A `pystray` tray icon runs on the main thread; `ApplauseDetector` (using `sounddevice` instead of `pyaudio`) runs on a daemon thread with a callback-based audio stream. When 2 claps are detected the detector calls `on_trigger`, which invokes `tts.speak()` and `launcher` functions. Config is stored in `~/.jarvis-launcher/config.json` and reloaded on each trigger.

**Tech Stack:** `sounddevice`, `numpy`, `scipy`, `edge-tts`, `pystray`, `Pillow`, `colorama`, `pyinstaller` (build-time), `pytest` (tests), `hatchling` (build backend).

---

## Task 1: Project scaffold + remove old files

**Files:**
- Create: `src/jarvis_launcher/__init__.py`
- Create: `pyproject.toml`
- Create: `tests/__init__.py`
- Delete: `src/applause_launcher.py`
- Delete: `run.sh`
- Delete: `install_applause.sh`
- Delete: `requirements.txt`

- [ ] **Step 1: Create the package directory and empty `__init__.py`**

```bash
mkdir -p src/jarvis_launcher tests
touch src/jarvis_launcher/__init__.py tests/__init__.py
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "jarvis-launcher"
version = "1.0.0"
description = "Two claps → JARVIS speaks → launches your workspace"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = [
    "sounddevice>=0.4.6",
    "numpy>=1.21.0",
    "scipy>=1.7.0",
    "edge-tts>=6.1.0",
    "pystray>=0.19.0",
    "Pillow>=9.0.0",
    "colorama>=0.4.6",
]

[project.optional-dependencies]
windows = ["playsound>=1.3.0", "pyttsx3>=2.90"]
dev = ["pytest>=7.0.0"]

[project.scripts]
jarvis-launcher = "jarvis_launcher.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/jarvis_launcher"]
```

- [ ] **Step 3: Install the package in editable mode with dev deps**

```bash
pip install -e ".[dev]"
```

Expected: installs sounddevice, numpy, scipy, edge-tts, pystray, Pillow, colorama, pytest.

- [ ] **Step 4: Remove old files**

```bash
rm src/applause_launcher.py run.sh install_applause.sh requirements.txt
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: scaffold jarvis_launcher package, remove old single-file script"
```

---

## Task 2: config.py — read/write `~/.jarvis-launcher/config.json`

**Files:**
- Create: `src/jarvis_launcher/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

`tests/test_config.py`:
```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch


def test_load_creates_defaults_when_no_file(tmp_path):
    config_file = tmp_path / "config.json"
    with patch("jarvis_launcher.config.CONFIG_FILE", config_file), \
         patch("jarvis_launcher.config.CONFIG_DIR", tmp_path):
        from jarvis_launcher import config
        result = config.load()
    assert result["sensitivity"] == 0.15
    assert result["required_claps"] == 2
    assert config_file.exists()


def test_load_reads_existing_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"sensitivity": 0.25, "required_claps": 3}))
    with patch("jarvis_launcher.config.CONFIG_FILE", config_file), \
         patch("jarvis_launcher.config.CONFIG_DIR", tmp_path):
        from jarvis_launcher import config
        result = config.load()
    assert result["sensitivity"] == 0.25
    assert result["required_claps"] == 3
    # defaults fill in missing keys
    assert result["open_claude_code"] is True


def test_load_merges_missing_keys_with_defaults(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"sensitivity": 0.10}))
    with patch("jarvis_launcher.config.CONFIG_FILE", config_file), \
         patch("jarvis_launcher.config.CONFIG_DIR", tmp_path):
        from jarvis_launcher import config
        result = config.load()
    assert result["sensitivity"] == 0.10
    assert "voice" in result
    assert "youtube_url" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `jarvis_launcher.config` doesn't exist yet.

- [ ] **Step 3: Implement `src/jarvis_launcher/config.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jarvis_launcher/config.py tests/test_config.py
git commit -m "feat: add config module with defaults and file persistence"
```

---

## Task 3: detector.py — clap detection with sounddevice

**Files:**
- Create: `src/jarvis_launcher/detector.py`
- Create: `tests/test_detector.py`

- [ ] **Step 1: Write failing tests**

`tests/test_detector.py`:
```python
import numpy as np
import pytest
from collections import deque
from unittest.mock import MagicMock, patch

CONFIG = {
    "sensitivity": 0.15,
    "noise_multiplier": 3.0,
    "required_claps": 2,
    "timeout_reset": 3.0,
    "min_seconds_between_claps": 0.3,
}


def _make_detector():
    from jarvis_launcher.detector import ApplauseDetector
    return ApplauseDetector(CONFIG, on_trigger=MagicMock())


def test_adaptive_threshold_returns_at_least_sensitivity():
    det = _make_detector()
    # noise_buf is seeded with 0.01 values
    threshold = det._adaptive_threshold()
    assert threshold >= CONFIG["sensitivity"]


def test_is_clap_returns_false_for_silence():
    det = _make_detector()
    silence = np.zeros(1024, dtype=np.float32)
    detected, rms = det._is_clap(silence)
    assert not detected
    assert rms == pytest.approx(0.0)


def test_is_clap_returns_false_for_low_frequency_noise():
    det = _make_detector()
    # Low-frequency sine at 100 Hz, high amplitude
    t = np.linspace(0, 1024 / 44100, 1024)
    signal = (0.5 * np.sin(2 * np.pi * 100 * t)).astype(np.float32)
    detected, rms = det._is_clap(signal)
    # High amplitude but wrong frequency band → not a clap
    assert not detected


def test_is_clap_returns_true_for_clap_like_signal():
    det = _make_detector()
    # Burst of white noise (clap-like: broadband, high amplitude)
    rng = np.random.default_rng(42)
    signal = (rng.uniform(-0.6, 0.6, 1024)).astype(np.float32)
    detected, rms = det._is_clap(signal)
    assert detected


def test_noise_buffer_updates_on_quiet_audio():
    det = _make_detector()
    initial_buf = list(det.noise_buf)
    silence = np.zeros(1024, dtype=np.float32)
    det._is_clap(silence)
    # Buffer should have a new 0.0 entry
    assert list(det.noise_buf) != initial_buf
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_detector.py -v
```

Expected: `ImportError` — `jarvis_launcher.detector` doesn't exist yet.

- [ ] **Step 3: Implement `src/jarvis_launcher/detector.py`**

```python
import threading
import time
from collections import deque

import numpy as np
import sounddevice as sd

RATE = 44100
CHUNK = 1024
FREQUENCY_MIN = 1000
FREQUENCY_MAX = 8000
NOISE_WINDOW_SECONDS = 5


class ApplauseDetector:
    def __init__(self, config: dict, on_trigger) -> None:
        self.config = config
        self.on_trigger = on_trigger
        self._busy = False
        self.claps_detected = 0
        self.last_clap_time = 0.0
        self._stream: sd.InputStream | None = None

        noise_buf_size = int(RATE / CHUNK * NOISE_WINDOW_SECONDS)
        self.noise_buf: deque[float] = deque([0.01] * noise_buf_size, maxlen=noise_buf_size)

    # ── Detection logic (pure — no I/O) ───────────────────────────────────────

    def _adaptive_threshold(self) -> float:
        arr = np.array(self.noise_buf)
        return max(
            self.config["sensitivity"],
            arr.mean() + self.config["noise_multiplier"] * arr.std(),
        )

    def _is_clap(self, audio: np.ndarray) -> tuple[bool, float]:
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < self._adaptive_threshold():
            self.noise_buf.append(rms)
            return False, rms

        fft_mag = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), d=1.0 / RATE)
        total_energy = np.sum(fft_mag) + 1e-10
        band_mask = (freqs >= FREQUENCY_MIN) & (freqs <= FREQUENCY_MAX)
        band_energy = np.sum(fft_mag[band_mask])
        return (band_energy / total_energy) > 0.25, rms

    # ── Audio callback (called from sounddevice thread) ────────────────────────

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if self._busy:
            return
        audio = indata[:, 0].astype(np.float32)
        detected, _ = self._is_clap(audio)
        if detected:
            now = time.time()
            min_gap = self.config["min_seconds_between_claps"]
            if now - self.last_clap_time > min_gap:
                self.claps_detected += 1
                self.last_clap_time = now
                if self.claps_detected >= self.config["required_claps"]:
                    self._busy = True
                    self.claps_detected = 0
                    threading.Thread(target=self._trigger, daemon=True).start()
        else:
            if (
                self.claps_detected > 0
                and time.time() - self.last_clap_time > self.config["timeout_reset"]
            ):
                self.claps_detected = 0

    def _trigger(self) -> None:
        try:
            self.on_trigger()
        finally:
            self._busy = False

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._stream = sd.InputStream(
            samplerate=RATE,
            channels=1,
            blocksize=CHUNK,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_detector.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jarvis_launcher/detector.py tests/test_detector.py
git commit -m "feat: add ApplauseDetector with sounddevice, port clap detection logic"
```

---

## Task 4: tts.py — cross-platform text-to-speech

**Files:**
- Create: `src/jarvis_launcher/tts.py`
- Create: `tests/test_tts.py`

- [ ] **Step 1: Write failing tests**

`tests/test_tts.py`:
```python
import sys
from unittest.mock import patch, MagicMock


def test_speak_falls_back_to_platform_fallback_on_edge_tts_failure():
    with patch("jarvis_launcher.tts._speak_edge_tts", side_effect=Exception("no internet")), \
         patch("jarvis_launcher.tts._speak_fallback") as mock_fallback:
        from jarvis_launcher import tts
        tts.speak("Hello sir")
        mock_fallback.assert_called_once_with("Hello sir")


def test_speak_edge_tts_is_called_first():
    with patch("jarvis_launcher.tts._speak_edge_tts") as mock_edge, \
         patch("jarvis_launcher.tts._speak_fallback") as mock_fallback:
        from jarvis_launcher import tts
        tts.speak("Hello sir", voice="en-GB-RyanNeural")
        mock_edge.assert_called_once_with("Hello sir", "en-GB-RyanNeural")
        mock_fallback.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_tts.py -v
```

Expected: `ImportError` — `jarvis_launcher.tts` doesn't exist yet.

- [ ] **Step 3: Implement `src/jarvis_launcher/tts.py`**

```python
import asyncio
import os
import subprocess
import sys
import tempfile

import edge_tts


def speak(text: str, voice: str = "en-GB-RyanNeural") -> None:
    try:
        _speak_edge_tts(text, voice)
    except Exception:
        _speak_fallback(text)


def _speak_edge_tts(text: str, voice: str) -> None:
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        async def _generate() -> None:
            communicate = edge_tts.Communicate(text, voice=voice, rate="+20%")
            await communicate.save(tmp.name)

        asyncio.run(_generate())
        _play_audio(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _play_audio(path: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(["afplay", path], check=False)
    elif sys.platform == "win32":
        try:
            from playsound import playsound  # type: ignore
            playsound(path)
        except Exception:
            pass
    else:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
            check=False,
        )


def _speak_fallback(text: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(["say", text], check=False)
    elif sys.platform == "win32":
        try:
            import pyttsx3  # type: ignore
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass
    else:
        subprocess.run(
            ["espeak-ng", "-v", "en-gb+m3", "-s", "170", "-p", "30", text],
            check=False,
            stderr=subprocess.DEVNULL,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_tts.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jarvis_launcher/tts.py tests/test_tts.py
git commit -m "feat: add cross-platform TTS module with edge-tts and platform fallbacks"
```

---

## Task 5: launcher.py — cross-platform app launching

**Files:**
- Create: `src/jarvis_launcher/launcher.py`
- Create: `tests/test_launcher.py`

- [ ] **Step 1: Write failing tests**

`tests/test_launcher.py`:
```python
import shutil
import sys
from unittest.mock import patch


def test_find_binary_returns_first_match():
    from jarvis_launcher.launcher import find_binary
    # "python3" or "python" must exist in any dev environment
    result = find_binary(["__nonexistent__", "python3", "python"])
    assert result in ("python3", "python")


def test_find_binary_returns_none_when_nothing_found():
    from jarvis_launcher.launcher import find_binary
    assert find_binary(["__definitely_not_here__"]) is None


def test_terminal_run_cmd_gnome_terminal():
    from jarvis_launcher.launcher import _terminal_run_cmd
    cmd = _terminal_run_cmd("gnome-terminal", "claude", "Claude Code")
    assert "gnome-terminal" in cmd
    assert "claude" in " ".join(cmd)


def test_terminal_run_cmd_xterm():
    from jarvis_launcher.launcher import _terminal_run_cmd
    cmd = _terminal_run_cmd("xterm", "claude", "Claude Code")
    assert cmd[0] == "xterm"
    assert "claude" in " ".join(cmd)


def test_open_youtube_calls_popen_with_url(monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.Popen", lambda cmd, **kw: calls.append(cmd))
    # Patch sys.platform to linux so it uses find_binary path
    with patch("jarvis_launcher.launcher.find_binary", return_value="firefox"), \
         patch("sys.platform", "linux"):
        from jarvis_launcher import launcher
        launcher.open_youtube("https://example.com")
    assert any("https://example.com" in str(c) for c in calls)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_launcher.py -v
```

Expected: `ImportError` — `jarvis_launcher.launcher` doesn't exist yet.

- [ ] **Step 3: Implement `src/jarvis_launcher/launcher.py`**

```python
import shutil
import subprocess
import sys

BROWSERS = [
    "google-chrome-stable",
    "google-chrome",
    "brave-browser",
    "chromium-browser",
    "chromium",
    "firefox",
]
TERMINAL_EMULATORS = ["gnome-terminal", "xterm", "konsole", "xfce4-terminal", "alacritty"]
BROWSER_NEW_WINDOW_FLAG: dict[str, str] = {
    "google-chrome-stable": "--new-window",
    "google-chrome": "--new-window",
    "brave-browser": "--new-window",
    "chromium-browser": "--new-window",
    "chromium": "--new-window",
    "firefox": "-new-window",
}


def find_binary(names: list[str]) -> str | None:
    for name in names:
        if shutil.which(name):
            return name
    return None


def open_claude_code() -> None:
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", "claude"])
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e",
            'tell app "Terminal" to do script "claude"'])
    else:
        terminal = find_binary(TERMINAL_EMULATORS)
        if terminal:
            subprocess.Popen(_terminal_run_cmd(terminal, "claude", "Claude Code"))


def open_cursor() -> None:
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", "cursor"])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "Cursor"])
    else:
        cursor = shutil.which("cursor") or "/usr/bin/cursor"
        subprocess.Popen([cursor])


def open_youtube(url: str) -> None:
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", url])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", url])
    else:
        browser = find_binary(BROWSERS)
        if browser:
            flag = BROWSER_NEW_WINDOW_FLAG.get(browser, "--new-window")
            subprocess.Popen([browser, flag, url])


def _terminal_run_cmd(terminal: str, shell_cmd: str, title: str = "") -> list[str]:
    if terminal == "gnome-terminal":
        base = ["gnome-terminal", "--title", title, "--"] if title else ["gnome-terminal", "--"]
        return base + ["bash", "-c", f'{shell_cmd}; echo ""; echo "  [Done] Press Enter."; read']
    if terminal == "xterm":
        args = ["-T", title] if title else []
        return ["xterm"] + args + ["-e", f"bash -c '{shell_cmd}; read'"]
    if terminal == "konsole":
        return ["konsole", "--new-tab", "-e", "bash", "-c", f"{shell_cmd}; read"]
    return [terminal, "-e", f"bash -c '{shell_cmd}; read'"]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_launcher.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jarvis_launcher/launcher.py tests/test_launcher.py
git commit -m "feat: add cross-platform launcher module"
```

---

## Task 6: tray.py + main.py — tray icon and entry point

**Files:**
- Create: `src/jarvis_launcher/tray.py`
- Create: `src/jarvis_launcher/main.py`

Note: pystray requires the main thread to own the icon loop. There are no unit tests for this module — its correctness is verified by running the app.

- [ ] **Step 1: Implement `src/jarvis_launcher/tray.py`**

```python
import random
import time

import pystray
from PIL import Image, ImageDraw

from . import config as cfg
from . import launcher
from . import tts
from .detector import ApplauseDetector

JARVIS_PHRASES = [
    "Good morning, sir. I trust everything is satisfactory.",
    "I am at your service, sir. All systems are online.",
    "Initialising workspace. Shall I prepare the workshop, sir?",
    "All systems nominal. Standing by for your instructions.",
    "A pleasure to assist you, sir. Let us begin.",
    "Workspace initialised. I await your command, sir.",
    "I'm quite sure you'll find this rather interesting, sir.",
]


def _create_icon() -> Image.Image:
    """Generate a simple green circle as the tray icon."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=(80, 200, 120, 255))
    return img


class JarvisTray:
    def __init__(self) -> None:
        self._config = cfg.load()
        self._detector: ApplauseDetector | None = None
        self._paused = False
        self._icon = pystray.Icon(
            "jarvis-launcher",
            _create_icon(),
            "JARVIS Launcher — Listening",
            menu=pystray.Menu(
                pystray.MenuItem(
                    lambda _: "⏸ Pause" if not self._paused else "▶ Resume",
                    self._toggle_pause,
                ),
                pystray.MenuItem("⚙ Open Settings", self._open_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("✕ Quit", self._quit),
            ),
        )

    # ── Trigger ───────────────────────────────────────────────────────────────

    def _on_trigger(self) -> None:
        self._config = cfg.load()  # pick up any config changes
        phrase = random.choice(JARVIS_PHRASES)
        tts.speak(phrase, self._config["voice"])
        if self._config["open_claude_code"]:
            launcher.open_claude_code()
            time.sleep(1)
        if self._config["open_cursor"]:
            launcher.open_cursor()
            time.sleep(2)
        if self._config["open_youtube"]:
            launcher.open_youtube(self._config["youtube_url"])

    # ── Menu actions ──────────────────────────────────────────────────────────

    def _toggle_pause(self, icon, item) -> None:
        self._paused = not self._paused
        if self._paused:
            if self._detector:
                self._detector.stop()
            icon.title = "JARVIS Launcher — Paused"
        else:
            if self._detector:
                self._detector.start()
            icon.title = "JARVIS Launcher — Listening"
        icon.update_menu()

    def _open_settings(self, icon, item) -> None:
        cfg.open_in_editor()

    def _quit(self, icon, item) -> None:
        if self._detector:
            self._detector.stop()
        icon.stop()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        self._detector = ApplauseDetector(self._config, self._on_trigger)
        self._detector.start()
        self._icon.run()  # blocks on main thread (required by pystray)
```

- [ ] **Step 2: Implement `src/jarvis_launcher/main.py`**

```python
from .tray import JarvisTray


def main() -> None:
    tray = JarvisTray()
    tray.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify the app starts without crashing**

```bash
timeout 3 jarvis-launcher || true
```

Expected: no Python traceback in the first 3 seconds (tray icon may not appear in headless CI, that's fine — test locally).

- [ ] **Step 4: Commit**

```bash
git add src/jarvis_launcher/tray.py src/jarvis_launcher/main.py
git commit -m "feat: add pystray tray icon and main entry point"
```

---

## Task 7: Run full test suite + update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASS (config: 3, detector: 5, tts: 2, launcher: 5 = 15 total).

- [ ] **Step 2: Update `CLAUDE.md` to reflect new structure**

Replace the contents of `CLAUDE.md` with:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

JARVIS Launcher listens for two consecutive claps via microphone and triggers a launch sequence: speaks a JARVIS phrase via TTS, opens Claude Code in a new terminal, opens Cursor, and opens a YouTube URL in a browser. Runs as a system tray icon on Linux, macOS, and Windows.

## Setup

System deps (Linux only):
```bash
sudo apt install portaudio19-dev ffmpeg
```

Install (editable + dev tools):
```bash
pip install -e ".[dev]"
```

## Running

```bash
jarvis-launcher
```

## Tests

```bash
pytest tests/ -v              # all tests
pytest tests/test_config.py   # single file
```

## Configuration

`~/.jarvis-launcher/config.json` — created with defaults on first run. Edit directly or use the tray menu "Open Settings".

Key fields: `sensitivity`, `noise_multiplier`, `required_claps`, `timeout_reset`, `open_claude_code`, `open_cursor`, `open_youtube`, `youtube_url`, `voice`.

## Architecture

```
src/jarvis_launcher/
├── main.py      # Entry point → JarvisTray.run()
├── tray.py      # pystray icon + menu; owns main thread
├── detector.py  # ApplauseDetector: sounddevice callback → clap logic → on_trigger()
├── launcher.py  # open_claude_code(), open_cursor(), open_youtube() — cross-platform
├── tts.py       # speak(): edge-tts primary, platform fallback (say/espeak-ng/pyttsx3)
└── config.py    # load() / open_in_editor() — ~/.jarvis-launcher/config.json
```

Thread model: tray icon runs on main thread (pystray requirement). Detector runs `sd.InputStream` in a sounddevice thread. On trigger, a daemon thread executes TTS + launcher so the audio callback returns immediately.

Config reloads on every trigger — changes to `config.json` take effect without restart.

## Distribution

```bash
pip install jarvis-launcher          # from PyPI
# or download binary from GitHub Releases (no Python needed)
```

Binaries built with PyInstaller via GitHub Actions on push to a `v*` tag.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for new package structure"
```

---

## Task 8: GitHub Actions — publish to PyPI

**Files:**
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Create `.github/workflows/publish.yml`**

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write   # required for Trusted Publisher (OIDC)
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

Note: before this workflow works, you must configure a Trusted Publisher on pypi.org for the repo. Go to pypi.org → Your account → Publishing → Add a new pending publisher. Fill in: PyPI project name `jarvis-launcher`, GitHub owner `francogalfre`, repo `jarvis-launcher`, workflow `publish.yml`, environment `pypi`.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/publish.yml
git commit -m "ci: add PyPI publish workflow on v* tags"
```

---

## Task 9: GitHub Actions — build standalone binaries

**Files:**
- Create: `.github/workflows/build.yml`

- [ ] **Step 1: Create `.github/workflows/build.yml`**

```yaml
name: Build Binaries

on:
  push:
    tags:
      - "v*"

permissions:
  contents: write   # needed to upload assets to GitHub Releases

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            artifact: jarvis-launcher-linux
          - os: macos-latest
            artifact: jarvis-launcher-macos
          - os: windows-latest
            artifact: jarvis-launcher-windows.exe

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install system deps (Linux)
        if: runner.os == 'Linux'
        run: sudo apt-get install -y portaudio19-dev ffmpeg

      - name: Install Python deps
        run: pip install pyinstaller sounddevice numpy scipy edge-tts pystray Pillow colorama

      - name: Install Windows extras
        if: runner.os == 'Windows'
        run: pip install playsound pyttsx3

      - name: Build binary
        run: >
          pyinstaller
          --onefile
          --name ${{ matrix.artifact }}
          --hidden-import jarvis_launcher
          src/jarvis_launcher/main.py

      - name: Upload to GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/${{ matrix.artifact }}*
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: add PyInstaller binary build workflow for Linux, macOS, Windows"
```

---

## Task 10: Final verification

- [ ] **Step 1: Run the full test suite one last time**

```bash
pytest tests/ -v
```

Expected: 15 tests PASS, 0 FAIL.

- [ ] **Step 2: Verify the package installs cleanly in a fresh venv**

```bash
python3 -m venv /tmp/test-jarvis
/tmp/test-jarvis/bin/pip install -e .
/tmp/test-jarvis/bin/jarvis-launcher --help 2>&1 || true
```

Expected: no import errors.

- [ ] **Step 3: Create and push the first release tag**

```bash
git tag v1.0.0
git push origin main --tags
```

Expected: GitHub Actions triggers both `publish.yml` and `build.yml`. Check the Actions tab on GitHub to confirm both workflows start.
