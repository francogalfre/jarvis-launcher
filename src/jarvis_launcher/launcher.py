import shutil
import subprocess
import sys

BROWSERS = [
    "google-chrome-stable",
    "google-chrome",
    "brave-browser",
    "chromium-browser",
    "chromium",
    "firefox",
]
TERMINAL_EMULATORS = ["gnome-terminal", "xterm", "konsole", "xfce4-terminal", "alacritty"]
BROWSER_NEW_WINDOW_FLAG: dict[str, str] = {
    "google-chrome-stable": "--new-window",
    "google-chrome": "--new-window",
    "brave-browser": "--new-window",
    "chromium-browser": "--new-window",
    "chromium": "--new-window",
    "firefox": "-new-window",
}


def find_binary(names: list[str]) -> str | None:
    for name in names:
        if shutil.which(name):
            return name
    return None


def open_claude_code() -> None:
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", "claude"])
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e",
            'tell app "Terminal" to do script "claude"'])
    else:
        terminal = find_binary(TERMINAL_EMULATORS)
        if terminal:
            subprocess.Popen(_terminal_run_cmd(terminal, "claude", "Claude Code"))


def open_cursor() -> None:
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", "cursor"])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "Cursor"])
    else:
        cursor = shutil.which("cursor") or "/usr/bin/cursor"
        subprocess.Popen([cursor])


def open_youtube(url: str) -> None:
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", url])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", url])
    else:
        browser = find_binary(BROWSERS)
        if browser:
            flag = BROWSER_NEW_WINDOW_FLAG.get(browser, "--new-window")
            subprocess.Popen([browser, flag, url])


def _terminal_run_cmd(terminal: str, shell_cmd: str, title: str = "") -> list[str]:
    if terminal == "gnome-terminal":
        base = ["gnome-terminal", "--title", title, "--"] if title else ["gnome-terminal", "--"]
        return base + ["bash", "-c", f'{shell_cmd}; echo ""; echo "  [Done] Press Enter."; read']
    if terminal == "xterm":
        args = ["-T", title] if title else []
        return ["xterm"] + args + ["-e", f"bash -c '{shell_cmd}; read'"]
    if terminal == "konsole":
        return ["konsole", "--new-tab", "-e", "bash", "-c", f"{shell_cmd}; read"]
    return [terminal, "-e", f"bash -c '{shell_cmd}; read'"]
