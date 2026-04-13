"""CLI module for jarvis-launcher."""
import argparse
import json
import sys
import time
from pathlib import Path

from jarvis_launcher import config as cfg


def _list_voices() -> None:
    """List available Edge TTS voices."""
    import asyncio
    import edge_tts

    async def _get_voices():
        voices = await edge_tts.list_voices()
        # Group by language
        by_lang: dict[str, list] = {}
        for v in voices:
            lang = v["Locale"]
            if lang not in by_lang:
                by_lang[lang] = []
            by_lang[lang].append(v["ShortName"])

        # Print organized by language
        for lang in sorted(by_lang.keys()):
            print(f"\n{lang}:")
            for short_name in sorted(by_lang[lang]):
                print(f"  {short_name}")

    asyncio.run(_get_voices())


def _show_config() -> None:
    """Show current configuration."""
    data = cfg.load()
    print(json.dumps(data, indent=2))


def _set_config(key: str, value: str) -> None:
    """Set a config value."""
    data = cfg.load()

    # Parse value based on key type
    if key in ("sensitivity", "noise_multiplier", "timeout_reset", "min_seconds_between_claps"):
        data[key] = float(value)
    elif key in ("required_claps",):
        data[key] = int(value)
    elif key in ("open_claude_code", "open_cursor", "open_youtube"):
        data[key] = value.lower() in ("true", "1", "yes", "on")
    else:
        data[key] = value

    cfg.CONFIG_FILE.write_text(json.dumps(data, indent=2))
    print(f"✓ Set {key} = {value}")


def _open_settings() -> None:
    """Open settings file in default editor."""
    cfg.open_in_editor()


def _test_mic() -> None:
    """Test microphone and show audio level."""
    import numpy as np
    import miniaudio

    print("🎤 Testing microphone...")
    print("   Speak or make noise to see levels.")
    print("   Press Ctrl+C to stop.\n")

    RATE = 44100
    CHUNK = 1024

    def callback(indata):
        audio = indata[:, 0].astype(np.float32)
        rms = float(np.sqrt(np.mean(audio ** 2)))
        bars = min(20, max(0, int(rms * 40)))
        filled = "█" * bars
        empty = "░" * (20 - bars)
        print(f"\r[{filled}{empty}] {rms:.3f}", end="", flush=True)

    try:
        device = miniaudio.CaptureDevice(
            input_format=miniaudio.SampleFormat.FLOAT32,
            nchannels=1,
            sample_rate=RATE,
            frames_per_buffer=CHUNK,
        )
        device.start(callback)
        print("   (recording... press Ctrl+C to stop)")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        device.close()
        print("\n\n✓ Microphone test complete")


def main() -> int:
    parser = argparse.ArgumentParser(prog="jarvis-launcher", description="JARVIS Launcher CLI")
    sub = parser.add_subparsers(dest="command", help="Commands")

    # jarvis-launcher voices
    sub.add_parser("voices", help="List available TTS voices")

    # jarvis-launcher config
    sub.add_parser("config", help="Show current configuration")

    # jarvis-launcher set <key> <value>
    set_parser = sub.add_parser("set", help="Set a config value")
    set_parser.add_argument("key", help="Config key")
    set_parser.add_argument("value", help="Config value")

    # jarvis-launcher open-settings
    sub.add_parser("open-settings", help="Open settings in editor")

    # jarvis-launcher test-mic
    sub.add_parser("test-mic", help="Test microphone and show audio levels")

    args = parser.parse_args()

    if args.command == "voices":
        _list_voices()
    elif args.command == "config":
        _show_config()
    elif args.command == "set":
        _set_config(args.key, args.value)
    elif args.command == "open-settings":
        _open_settings()
    elif args.command == "test-mic":
        _test_mic()
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())