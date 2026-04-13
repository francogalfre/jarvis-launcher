import sys
from unittest.mock import patch


def test_find_binary_returns_first_match():
    from jarvis_launcher.launcher import find_binary
    result = find_binary(["__nonexistent__", "python3", "python"])
    assert result in ("python3", "python")


def test_find_binary_returns_none_when_nothing_found():
    from jarvis_launcher.launcher import find_binary
    assert find_binary(["__definitely_not_here__"]) is None


def test_terminal_run_cmd_gnome_terminal():
    from jarvis_launcher.launcher import _terminal_run_cmd
    cmd = _terminal_run_cmd("gnome-terminal", "claude", "Claude Code")
    assert "gnome-terminal" in cmd
    assert "claude" in " ".join(cmd)


def test_terminal_run_cmd_xterm():
    from jarvis_launcher.launcher import _terminal_run_cmd
    cmd = _terminal_run_cmd("xterm", "claude", "Claude Code")
    assert cmd[0] == "xterm"
    assert "claude" in " ".join(cmd)


def test_open_youtube_calls_popen_with_url(monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.Popen", lambda cmd, **kw: calls.append(cmd))
    with patch("jarvis_launcher.launcher.find_binary", return_value="firefox"), \
         patch("sys.platform", "linux"):
        from jarvis_launcher import launcher
        launcher.open_youtube("https://example.com")
    assert any("https://example.com" in str(c) for c in calls)
