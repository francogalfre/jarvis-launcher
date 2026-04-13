# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

JARVIS Launcher listens for two consecutive claps via microphone and triggers a launch sequence: speaks a JARVIS phrase via TTS, opens Claude Code in a new terminal, opens Cursor, and opens a YouTube URL in a browser.

## Running

```bash
bash run.sh          # auto-installs on first run, then starts the detector
# or after install:
applause             # shell alias added to ~/.bashrc and ~/.zshrc by installer
```

Manual:
```bash
.venv/bin/python src/applause_launcher.py
```

## Setup

```bash
bash install_applause.sh   # installs system deps (portaudio19-dev, ffmpeg, espeak-ng), creates .venv, adds alias
```

System requirements: `portaudio19-dev`, `ffmpeg`, `espeak-ng` (fallback TTS), working microphone.

## Configuration

All tunable constants live at the top of `src/applause_launcher.py`:

- `THRESHOLD_AMPLITUDE` / `NOISE_ADAPTIVE_MULTIPLIER` — clap sensitivity
- `FREQUENCY_MIN` / `FREQUENCY_MAX` — spectral band for clap detection (default 1–8 kHz)
- `MIN_SECONDS_BETWEEN_CLAPS` / `TIMEOUT_RESET` — timing windows
- `YOUTUBE_URL` — song to open
- `BROWSERS` / `TERMINAL_EMULATORS` — preference-ordered binary lists (first found wins)
- `JARVIS_PHRASES` — list of spoken greetings

## Architecture

Single file: `src/applause_launcher.py`.

**Detection pipeline** (`ApplauseDetector`):
1. PyAudio streams raw float32 audio in 1024-sample chunks at 44100 Hz
2. Each chunk is checked via `_is_clap()`: RMS vs adaptive threshold, then FFT energy ratio in 1–8 kHz band must exceed 25%
3. Background noise is tracked in a rolling buffer; adaptive threshold = `noise_mean + N * noise_std`
4. Two claps within `TIMEOUT_RESET` seconds trigger `_execute_jarvis()`

**Launch sequence** (`_execute_jarvis`):
1. TTS via `edge-tts` (`en-GB-RyanNeural`), played with `ffplay`; falls back to `espeak-ng`
2. Opens Claude Code in a new terminal window
3. Opens Cursor (`/usr/bin/cursor`) pointing to `PROJECT_ROOT`
4. Opens YouTube in the first detected browser

**Helper functions** (`_terminal_run_cmd`, `_terminal_cwd_cmd`) build terminal launch commands per emulator (gnome-terminal, xterm, konsole, xfce4-terminal, alacritty).
