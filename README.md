# JARVIS Launcher

Clap twice → JARVIS speaks → your workspace opens automatically.

Detects two consecutive claps via microphone and launches Claude Code, Cursor, and a YouTube song of your choice. Runs as a background app with a system tray icon on Linux, macOS, and Windows.

## Install

```bash
pip install jarvis-launcher
jarvis-launcher
```

No system dependencies required on any platform.

## Download binary (no Python needed)

Grab the latest binary from [Releases](https://github.com/francogalfre/jarvis-launcher/releases).

| Platform | File |
|----------|------|
| Linux    | `jarvis-launcher-linux` |
| macOS    | `jarvis-launcher-macos` |
| Windows  | `jarvis-launcher-windows.exe` |

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
