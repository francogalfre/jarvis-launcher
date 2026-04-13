import random
import time

import pystray
from PIL import Image, ImageDraw

from . import config as cfg
from . import launcher
from . import tts
from .detector import ApplauseDetector

JARVIS_PHRASES = [
    "Good morning, sir. I trust everything is satisfactory.",
    "I am at your service, sir. All systems are online.",
    "Initialising workspace. Shall I prepare the workshop, sir?",
    "All systems nominal. Standing by for your instructions.",
    "A pleasure to assist you, sir. Let us begin.",
    "Workspace initialised. I await your command, sir.",
    "I'm quite sure you'll find this rather interesting, sir.",
]


def _create_icon() -> Image.Image:
    """Generate a simple green circle as the tray icon."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=(80, 200, 120, 255))
    return img


class JarvisTray:
    def __init__(self) -> None:
        self._config = cfg.load()
        self._detector: ApplauseDetector | None = None
        self._paused = False
        self._icon = pystray.Icon(
            "jarvis-launcher",
            _create_icon(),
            "JARVIS Launcher - Listening",
            menu=pystray.Menu(
                pystray.MenuItem(
                    lambda _: "⏸ Pause" if not self._paused else "▶ Resume",
                    self._toggle_pause,
                ),
                pystray.MenuItem("⚙ Open Settings", self._open_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("✕ Quit", self._quit),
            ),
        )

    def _on_trigger(self) -> None:
        self._config = cfg.load()
        phrase = random.choice(JARVIS_PHRASES)
        tts.speak(phrase, self._config["voice"])
        if self._config["open_claude_code"]:
            launcher.open_claude_code()
            time.sleep(1)
        if self._config["open_cursor"]:
            launcher.open_cursor()
            time.sleep(2)
        if self._config["open_youtube"]:
            launcher.open_youtube(self._config["youtube_url"])

    def _toggle_pause(self, icon, item) -> None:
        self._paused = not self._paused
        if self._paused:
            if self._detector:
                self._detector.stop()
            icon.title = "JARVIS Launcher - Paused"
        else:
            if self._detector:
                self._detector.start()
            icon.title = "JARVIS Launcher - Listening"
        icon.update_menu()

    def _open_settings(self, icon, item) -> None:
        cfg.open_in_editor()

    def _quit(self, icon, item) -> None:
        if self._detector:
            self._detector.stop()
        icon.stop()

    def run(self) -> None:
        self._detector = ApplauseDetector(self._config, self._on_trigger)
        self._detector.start()
        print("JARVIS Launcher is running. Clap twice to activate.")
        print("Right-click the tray icon to pause, open settings, or quit.")
        self._icon.run()
