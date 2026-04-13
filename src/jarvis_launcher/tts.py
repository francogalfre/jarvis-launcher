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
        # playsound 1.3.0 is broken on Python 3.12 — raise so speak() falls back to pyttsx3
        raise RuntimeError("ffplay not available; falling back to pyttsx3")
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
