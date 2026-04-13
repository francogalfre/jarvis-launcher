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
    import threading
    import miniaudio

    done = threading.Event()

    def samples():
        yield from miniaudio.stream_file(path)
        done.set()

    with miniaudio.PlaybackDevice() as device:
        device.start(samples())
        done.wait()


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
