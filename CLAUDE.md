# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

JARVIS Launcher listens for two consecutive claps via microphone and triggers a launch sequence: speaks a JARVIS phrase via TTS, opens Claude Code in a new terminal, opens Cursor, and opens a YouTube URL in a browser. Runs as a system tray icon on Linux, macOS, and Windows.

## Setup

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

`~/.jarvis-launcher/config.json` — created with defaults on first run. Edit directly or via tray menu "Open Settings".

Key fields: `sensitivity`, `noise_multiplier`, `required_claps`, `timeout_reset`, `open_claude_code`, `open_cursor`, `open_youtube`, `youtube_url`, `voice`.

## Architecture

```
src/jarvis_launcher/
├── main.py      # Entry point → JarvisTray.run()
├── tray.py      # pystray icon + menu; owns main thread
├── detector.py  # ApplauseDetector: soundcard loop → clap logic → on_trigger()
├── launcher.py  # open_claude_code(), open_cursor(), open_youtube() — cross-platform
├── tts.py       # speak(): edge-tts primary, platform fallback (say/espeak-ng/pyttsx3)
└── config.py    # load() / open_in_editor() — ~/.jarvis-launcher/config.json
```

Thread model: tray icon runs on main thread (pystray requirement). Detector runs a soundcard recording loop in a daemon thread. On trigger, a daemon thread executes TTS + launcher so the recording loop returns immediately.

Config reloads on every trigger — changes to `config.json` take effect without restart.

## Distribution

```bash
pip install jarvis-launcher          # from PyPI
# or download binary from GitHub Releases (no Python needed)
```

Binaries built with PyInstaller via GitHub Actions on push to a `v*` tag.
