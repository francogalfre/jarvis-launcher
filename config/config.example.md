# JARVIS Launcher — Configuration Guide

All settings live at the top of `src/applause_launcher.py`.

---

## Sensitivity

```python
THRESHOLD_AMPLITUDE = 0.15        # Base floor (0.05–0.30)
NOISE_ADAPTIVE_MULTIPLIER = 3.0   # threshold = noise_mean + N * noise_std
```

| Value | Use case |
|-------|----------|
| 0.08  | Very sensitive — quiet rooms, weak claps |
| 0.12  | Sensitive — good default for quiet offices |
| 0.15  | Normal — balanced (default) |
| 0.20  | Less sensitive — noisy environments |
| 0.30  | Low — only very loud claps |

Lower `NOISE_ADAPTIVE_MULTIPLIER` (e.g. 2.0) → more sensitive.
Higher (e.g. 4.0) → fewer false positives.

---

## Frequency Range

```python
FREQUENCY_MIN = 1000   # Hz
FREQUENCY_MAX = 8000   # Hz
```

Claps sit mostly between 1–8 kHz. Widen the range if detection misses.

---

## Timing

```python
MIN_SECONDS_BETWEEN_CLAPS = 0.3   # Ignore bursts faster than this
TIMEOUT_RESET = 3.0               # Seconds of silence resets clap counter
```

---

## YouTube URL

```python
YOUTUBE_URL = "https://www.youtube.com/watch?v=4xDzrJKXOOY"
```

Paste any YouTube URL here.

---

## Browser Preference

```python
BROWSERS = ["firefox", "google-chrome", "brave-browser", "chromium-browser", "chromium"]
```

First installed browser in this list wins. Reorder to change preference.

---

## JARVIS Phrases

```python
JARVIS_PHRASES = [
    "Good morning, sir. I trust everything is satisfactory.",
    # Add your own phrases here…
]
```

Phrases use British English (en-GB) via gTTS. Keep them short for faster TTS.

---

## Voice

gTTS uses Google's TTS engine with `tld="co.uk"` for the British accent.
To change language/accent, edit `_speak()` in `applause_launcher.py`:

```python
tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
```

| `tld`    | Accent      |
|----------|-------------|
| `co.uk`  | British     |
| `com.au` | Australian  |
| `com`    | American    |

---

## Troubleshooting

**No claps detected?**
- Decrease `THRESHOLD_AMPLITUDE` to `0.10`
- Decrease `NOISE_ADAPTIVE_MULTIPLIER` to `2.0`

**Too many false positives?**
- Increase `THRESHOLD_AMPLITUDE` to `0.25`
- Increase `NOISE_ADAPTIVE_MULTIPLIER` to `4.0`

**TTS not working?**
- Ensure internet connection (gTTS is online)
- Install `mpg123`: `sudo apt-get install mpg123`
- Or install `ffmpeg`: `sudo apt-get install ffmpeg`

**Browser not opening in new window?**
- Check `BROWSERS` list matches your installed browser binary name
- Run `which firefox` (or chrome/brave) to confirm the binary name
