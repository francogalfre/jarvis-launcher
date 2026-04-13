import os
import sys

# On Linux, add system dist-packages so pystray can use the GTK backend
# (gi/PyGObject is a system library not installable via pip)
if sys.platform == "linux":
    _sys_pkgs = "/usr/lib/python3/dist-packages"
    if _sys_pkgs not in sys.path:
        sys.path.insert(0, _sys_pkgs)
    os.environ.setdefault("PYSTRAY_BACKEND", "gtk")

from .tray import JarvisTray


def main() -> None:
    tray = JarvisTray()
    tray.run()


if __name__ == "__main__":
    main()
