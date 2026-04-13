import os
import sys

if sys.platform == "linux":
    _sys_pkgs = "/usr/lib/python3/dist-packages"
    if _sys_pkgs not in sys.path:
        sys.path.insert(0, _sys_pkgs)
    os.environ.setdefault("PYSTRAY_BACKEND", "gtk")
    # Suppress deprecation warnings from Gtk.StatusIcon
    from gi.repository import GLib
    GLib.log_set_handler(
        "Gtk",
        GLib.LogLevelFlags.LEVEL_CRITICAL | GLib.LogLevelFlags.LEVEL_WARNING,
        lambda *_: None,
        None,
    )

from .tray import JarvisTray


def main() -> None:
    tray = JarvisTray()
    tray.run()


if __name__ == "__main__":
    main()
