# JARVIS Launcher

Clap twice → JARVIS speaks → your workspace opens automatically.

## Install

```bash
pip install jarvis-launcher
```

## Usage

```bash
jarvis-launcher
```

A tray icon appears. The terminal shows microphone levels in real-time:

```
[████████░░░░░░░░] 👏👏
```

Right-click the tray icon to pause/resume, open settings, or quit.

### CLI commands

```bash
jarvis config              # Show current configuration
jarvis set voice en-US-JennyNeural  # Change voice
jarvis voices             # List popular TTS voices
jarvis open-settings     # Open config in editor
jarvis test-mic          # Test microphone
```

## Configuration

Settings are in `~/.jarvis-launcher/config.json`:

```json
{
  "sensitivity": 0.15,
  "required_claps": 2,
  "open_claude_code": true,
  "open_cursor": true,
  "open_youtube": true,
  "youtube_url": "https://www.youtube.com/watch?v=v2AC41dglnM",
  "voice": "en-GB-RyanNeural",
  "phrases": [
    "Good morning, sir. I trust everything is satisfactory.",
    "I am at your service, sir. All systems are online."
  ]
}
```

| Setting | Description | Default |
|---------|-------------|---------|
| `sensitivity` | Mic sensitivity (0.05-0.5) | 0.15 |
| `required_claps` | Claps needed to trigger | 2 |
| `voice` | Edge TTS voice | en-GB-RyanNeural |
| `phrases` | Custom phrases | [defaults] |

**Environment sensitivity:**

| Value | Setting |
|------|---------|
| `0.08` | Quiet room |
| `0.15` | Normal office |
| `0.25` | Noisy room |

## Download binary

Download the latest binary from [Releases](https://github.com/francogalfre/jarvis-launcher/releases) - no Python needed.

## License

MIT