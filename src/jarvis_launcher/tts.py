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
        _play_audio_subprocess(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _play_audio_subprocess(path: str) -> None:
    """Play audio using system player to avoid miniaudio conflicts."""
    if sys.platform == "darwin":
        subprocess.run(["afplay", path], check=False)
    elif sys.platform == "win32":
        # Try multiple players
        for player in ["powershell", "start"]:
            if player == "start":
                subprocess.run(["cmd", "/c", "start", "/b", "msplays", path], check=False)
                return
        subprocess.run(["powershell", "-c", f"(New-Object System.Media.SoundPlayer '{path}').PlaySync()"], check=False)
    else:
        # Linux - try mplayer, aplay, mpg123, or paplay
        for player in ["mplayer", "mpg123", "aplay", "paplay"]:
            if subprocess.run(["which", player], capture_output=True).returncode == 0:
                subprocess.run([player, path], check=False)
                return
        # Last resort: use python with simpleaudio if available
        _speak_fallback_using_py(path)


def _speak_fallback_using_py(path: str) -> None:
    """Try using python modules for playback."""
    try:
        import simpleaudio as sa
        wave_obj = sa.WaveObject.from_wave_file(path)
        wave_obj.play().wait_done()
        return
    except ImportError:
        pass
    # Fallback to espeak
    _speak_fallback("")


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
