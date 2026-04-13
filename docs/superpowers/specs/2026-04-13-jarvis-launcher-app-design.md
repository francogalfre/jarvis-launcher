# Design: jarvis-launcher — Cross-Platform Tray App

**Date:** 2026-04-13
**Status:** Approved

## Overview

Transform the existing single-file Python clap-detection script into a proper cross-platform application: a background process with a system tray icon, installable via `pip install jarvis-launcher` or as a standalone binary (no Python required).

**Goal:** Two claps → JARVIS speaks → launches configured apps. Available on Linux, macOS, and Windows.

---

## 1. Project Structure

```
jarvis-launcher/
├── src/
│   └── jarvis_launcher/
│       ├── __init__.py
│       ├── main.py          # Entry point: starts tray icon + detector threads
│       ├── detector.py      # ApplauseDetector — audio stream + clap detection
│       ├── launcher.py      # Executes actions (Claude Code, Cursor, YouTube, etc.)
│       ├── tts.py           # Text-to-speech: edge-tts + platform fallbacks
│       ├── config.py        # Reads/writes ~/.jarvis-launcher/config.json
│       └── tray.py          # pystray icon + menu (Start, Stop, Settings, Quit)
├── assets/
│   └── icon.png             # Tray icon (required by pystray)
├── pyproject.toml
├── .github/
│   └── workflows/
│       ├── publish.yml      # Publish to PyPI on release tag push
│       └── build.yml        # PyInstaller → binaries attached to GitHub Releases
└── CLAUDE.md
```

**Thread model:** `main.py` runs the tray icon on the main thread (required by pystray) and the `ApplauseDetector` on a daemon thread. When 2 claps are detected, `detector.py` calls `launcher.py` with the configured actions. The detector reloads config on each trigger cycle so changes to `config.json` take effect without restart.

---

## 2. Configuration

Stored at `~/.jarvis-launcher/config.json`, created with defaults on first run.

```json
{
  "sensitivity": 0.15,
  "noise_multiplier": 3.0,
  "required_claps": 2,
  "timeout_reset": 3.0,
  "youtube_url": "https://www.youtube.com/watch?v=v2AC41dglnM",
  "open_claude_code": true,
  "open_cursor": true,
  "open_youtube": true,
  "voice": "en-GB-RyanNeural"
}
```

**Settings UX:** The tray menu "Open Settings" opens `config.json` with the system's default editor (`xdg-open` on Linux, `open` on macOS, `start` on Windows). No custom settings GUI needed.

**Extensibility note:** `launcher.py` is designed so that adding new launch targets (VSCode, custom scripts, etc.) requires only adding a new boolean key to config and a corresponding method — no structural changes.

---

## 3. Tray Menu

```
● Listening...        ← dynamic status line
──────────────────
⏸ Pause / ▶ Resume
⚙ Open Settings
──────────────────
✕ Quit
```

Status cycles between: `Listening...`, `Paused`, `🚀 Launching...`

---

## 4. Cross-Platform Audio & TTS

**Audio input:** Replace `pyaudio` with `sounddevice` — uses CoreAudio on macOS, WASAPI on Windows, ALSA/PulseAudio on Linux. No system library install required on macOS/Windows.

**TTS chain per platform:**

| Platform | Primary | Fallback |
|----------|---------|---------|
| Linux    | edge-tts → ffplay | espeak-ng |
| macOS    | edge-tts → afplay | say (built-in) |
| Windows  | edge-tts → playsound | pyttsx3 |

---

## 5. Distribution

### PyPI
- `pyproject.toml` defines `[project.scripts]: jarvis-launcher = "jarvis_launcher.main:main"`
- Dependencies: `sounddevice`, `numpy`, `scipy`, `edge-tts`, `pystray`, `colorama`, `Pillow`
- Linux users must install system deps: `sudo apt install portaudio19-dev ffmpeg`
- macOS/Windows: no system deps needed
- GitHub Actions `publish.yml` triggers on `v*` tag push → builds and uploads to PyPI via Trusted Publisher

### GitHub Releases (binaries)
- `build.yml` matrix: `ubuntu-latest`, `macos-latest`, `windows-latest`
- PyInstaller `--onefile` bundles Python + all deps into a single executable
- Artifacts: `jarvis-launcher-linux`, `jarvis-launcher-macos`, `jarvis-launcher-windows.exe`
- Users download and run — no Python installation required

### README install section
```
pip install jarvis-launcher

# or download the binary from GitHub Releases (no Python needed)
```
