import numpy as np
import pytest
from unittest.mock import MagicMock

CONFIG = {
    "sensitivity": 0.15,
    "noise_multiplier": 3.0,
    "required_claps": 2,
    "timeout_reset": 3.0,
    "min_seconds_between_claps": 0.3,
}


def _make_detector():
    from jarvis_launcher.detector import ApplauseDetector
    return ApplauseDetector(CONFIG, on_trigger=MagicMock())


def test_adaptive_threshold_returns_at_least_sensitivity():
    det = _make_detector()
    threshold = det._adaptive_threshold()
    assert threshold >= CONFIG["sensitivity"]


def test_is_clap_returns_false_for_silence():
    det = _make_detector()
    silence = np.zeros(1024, dtype=np.float32)
    detected, rms = det._is_clap(silence)
    assert not detected
    assert rms == pytest.approx(0.0)


def test_is_clap_returns_false_for_low_frequency_noise():
    det = _make_detector()
    t = np.linspace(0, 1024 / 44100, 1024)
    signal = (0.5 * np.sin(2 * np.pi * 100 * t)).astype(np.float32)
    detected, rms = det._is_clap(signal)
    assert not detected


def test_is_clap_returns_true_for_clap_like_signal():
    det = _make_detector()
    rng = np.random.default_rng(42)
    signal = (rng.uniform(-0.6, 0.6, 1024)).astype(np.float32)
    detected, rms = det._is_clap(signal)
    assert detected


def test_noise_buffer_updates_on_quiet_audio():
    det = _make_detector()
    initial_buf = list(det.noise_buf)
    silence = np.zeros(1024, dtype=np.float32)
    det._is_clap(silence)
    assert list(det.noise_buf) != initial_buf
