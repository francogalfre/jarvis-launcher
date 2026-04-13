import random
import threading
import time
from typing import Callable

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


def _create_icon(color: tuple[int, int, int, int] = (80, 200, 120, 255)) -> Image.Image:
    """Generate a simple colored circle as the tray icon."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img


class MicIndicator:
    """Console microphone level indicator."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._level = 0.0
        self._running = False
        self._thread: threading.Thread | None = None

    def update(self, level: float) -> None:
        with self._lock:
            self._level = level

    def _render(self) -> str:
        with self._lock:
            # level is 0.0 to ~1.0, map to 10 bars
            bars = min(10, max(0, int(self._level * 20)))
        if bars == 0:
            return "○ ○ ○ ○ ○ ○ ○ ○ ○ ○"
        filled = "●" * bars
        empty = "○" * (10 - bars)
        return f"{filled}{empty}"

    def __str__(self) -> str:
        return self._render()


# Global indicator instance
_mic_indicator = MicIndicator()


def get_mic_indicator() -> MicIndicator:
    return _mic_indicator


def _print_status(mic_level: float, detected: bool = False) -> None:
    """Print status line with mic level."""
    indicator = get_mic_indicator()
    indicator.update(mic_level)
    status = "🎤" if detected else "  "
    print(f"\r[{indicator}] {status}", end="", flush=True)


class JarvisTray:
    def __init__(self) -> None:
        self._config = cfg.load()
        self._detector: ApplauseDetector | None = None
        self._paused = False
        self._running = False
        self._status_thread: threading.Thread | None = None
        
        # Icon colors for different states
        self._colors = {
            "listening": (80, 200, 120, 255),   # green
            "detecting": (255, 200, 0, 255),   # yellow
            "paused": (128, 128, 128, 255),    # gray
            "triggered": (255, 100, 100, 255), # red
        }
        
        self._icon = pystray.Icon(
            "jarvis-launcher",
            _create_icon(self._colors["listening"]),
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
        
        # For audio level updates
        self._last_level = 0.0
        self._claps_count = 0

    def _update_status_line(self) -> None:
        """Continuously print mic level in terminal."""
        indicator = get_mic_indicator()
        while self._running and not self._paused:
            # Show level from detector
            level = self._last_level
            bars = min(10, max(0, int(level * 20)))
            if bars == 0:
                bars_str = "○ ○ ○ ○ ○ ○ ○ ○ ○ ○"
            else:
                filled = "●" * bars
                empty = "○" * (10 - bars)
                bars_str = f"{filled}{empty}"
            
            claps = "🔔" * self._claps_count if self._claps_count else ""
            print(f"\r[{bars_str}] {claps}", end="", flush=True)
            time.sleep(0.1)
        # Print paused state
        if self._paused:
            print(f"\r[⏸ PAUSED]   Say 'pause' in config to resume")

    def _on_audio_level(self, level: float) -> None:
        """Update mic level indicator in console."""
        self._last_level = level

    def _on_clap_detected(self, count: int) -> None:
        """Called when a clap is detected."""
        self._claps_count = count
        print(f"\r  👏 Clap {count}/{self._config['required_claps']} detected!")

    def _on_trigger(self) -> None:
        # Update icon to show triggered state
        self._icon.icon = _create_icon(self._colors["triggered"])
        
        self._config = cfg.load()
        phrase = random.choice(JARVIS_PHRASES)
        
        print(f"\n🔥 TRIGGERED! Detected {self._config['required_claps']} claps")
        print(f"   JARVIS says: \"{phrase}\"")
        
        tts.speak(phrase, self._config["voice"])
        
        if self._config["open_claude_code"]:
            launcher.open_claude_code()
            time.sleep(1)
        if self._config["open_cursor"]:
            launcher.open_cursor()
            time.sleep(2)
        if self._config["open_youtube"]:
            launcher.open_youtube(self._config["youtube_url"])
        
        # Reset icon to listening
        self._icon.icon = _create_icon(self._colors["listening"])

    def _toggle_pause(self, icon, item) -> None:
        self._paused = not self._paused
        if self._paused:
            if self._detector:
                self._detector.stop()
            icon.title = "JARVIS Launcher - Paused"
            icon.icon = _create_icon(self._colors["paused"])
        else:
            if self._detector:
                self._detector.start()
            icon.title = "JARVIS Launcher - Listening"
            icon.icon = _create_icon(self._colors["listening"])
        icon.update_menu()

    def _open_settings(self, icon, item) -> None:
        cfg.open_in_editor()

    def _quit(self, icon, item) -> None:
        if self._detector:
            self._detector.stop()
        icon.stop()

    def run(self) -> None:
        self._running = True
        
        # Print welcome message
        print("=" * 50)
        print("🤖 JARVIS Launcher v1.0")
        print("=" * 50)
        print()
        print("📋 Status:")
        print(f"   • Sensitivity: {self._config['sensitivity']}")
        print(f"   • Required claps: {self._config['required_claps']}")
        print(f"   • Voice: {self._config['voice']}")
        print()
        print("🟢 Listening for claps...")
        print("   (clap twice to trigger)")
        print()
        print("💡 Tip: Right-click tray icon to pause or open settings")
        print("-" * 50)
        
        # Start detector with callbacks
        self._detector = ApplauseDetector(
            self._config, 
            self._on_trigger,
            on_audio_level=self._on_audio_level,
            on_clap=self._on_clap_detected
        )
        self._detector.start()
        
        # Start status display thread
        self._status_thread = threading.Thread(target=self._update_status_line, daemon=True)
        self._status_thread.start()
        
        self._icon.run()
