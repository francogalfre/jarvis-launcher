# JARVIS Launcher

Clap twice → JARVIS speaks → your workspace opens automatically.

Detects two consecutive claps via microphone and launches Claude Code, Cursor, and a YouTube song of your choice. Runs as a background app with a system tray icon on Linux, macOS, and Windows.

## Download

Grab the latest binary from [Releases](https://github.com/francogalfre/jarvis-launcher/releases) — no Python required.

| Platform | File |
|----------|------|
| Linux    | `jarvis-launcher-linux` |
| macOS    | `jarvis-launcher-macos` |
| Windows  | `jarvis-launcher-windows.exe` |

## Install from source

**Linux system deps:**
```bash
sudo apt install portaudio19-dev ffmpeg
```

```bash
pip install -e ".[dev]"
jarvis-launcher
```

## Usage

1. Run `jarvis-launcher` — a green tray icon appears
2. Clap twice in front of your microphone
3. JARVIS speaks, then opens Claude Code, Cursor, and YouTube

Right-click the tray icon to pause/resume, open settings, or quit.

## Configuration

Settings live in `~/.jarvis-launcher/config.json` (created on first run). Open it via the tray menu or edit directly:

```json
{
  "sensitivity": 0.15,
  "required_claps": 2,
  "open_claude_code": true,
  "open_cursor": true,
  "open_youtube": true,
  "youtube_url": "https://www.youtube.com/watch?v=v2AC41dglnM",
  "voice": "en-GB-RyanNeural"
}
```

**Sensitivity tuning:**

| Value | Environment |
|-------|-------------|
| `0.08` | Very quiet room |
| `0.15` | Normal office (default) |
| `0.25` | Noisy environment |

Changes take effect on the next clap trigger — no restart needed.

## How it works

- Streams microphone audio in 1024-sample chunks at 44100 Hz
- Each chunk is checked for clap signature: high RMS + energy concentrated in the 1–8 kHz band (>25% of total)
- Adaptive threshold adjusts to background noise automatically
- Two claps within 3 seconds trigger the launch sequence

## License

MIT
