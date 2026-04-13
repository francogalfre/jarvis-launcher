import threading
import time
from collections import deque

import numpy as np

RATE = 44100
CHUNK = 1024
FREQUENCY_MIN = 1000
FREQUENCY_MAX = 8000
NOISE_WINDOW_SECONDS = 5


class ApplauseDetector:
    def __init__(self, config: dict, on_trigger) -> None:
        self.config = config
        self.on_trigger = on_trigger
        self._busy = False
        self.claps_detected = 0
        self.last_clap_time = 0.0
        self._running = False
        self._thread = None

        noise_buf_size = int(RATE / CHUNK * NOISE_WINDOW_SECONDS)
        self.noise_buf: deque[float] = deque([0.01] * noise_buf_size, maxlen=noise_buf_size)

    def _adaptive_threshold(self) -> float:
        arr = np.array(self.noise_buf)
        return max(
            self.config["sensitivity"],
            arr.mean() + self.config["noise_multiplier"] * arr.std(),
        )

    def _is_clap(self, audio: np.ndarray) -> tuple[bool, float]:
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < self._adaptive_threshold():
            self.noise_buf.append(rms)
            return False, rms

        fft_mag = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), d=1.0 / RATE)
        total_energy = np.sum(fft_mag) + 1e-10
        band_mask = (freqs >= FREQUENCY_MIN) & (freqs <= FREQUENCY_MAX)
        band_energy = np.sum(fft_mag[band_mask])
        return (band_energy / total_energy) > 0.25, rms

    def _audio_callback(self, indata) -> None:
        if self._busy:
            return
        audio = indata[:, 0].astype(np.float32)
        detected, _ = self._is_clap(audio)
        if detected:
            now = time.time()
            min_gap = self.config["min_seconds_between_claps"]
            if now - self.last_clap_time > min_gap:
                self.claps_detected += 1
                self.last_clap_time = now
                if self.claps_detected >= self.config["required_claps"]:
                    self._busy = True
                    self.claps_detected = 0
                    threading.Thread(target=self._trigger, daemon=True).start()
        else:
            if (
                self.claps_detected > 0
                and time.time() - self.last_clap_time > self.config["timeout_reset"]
            ):
                self.claps_detected = 0

    def _trigger(self) -> None:
        try:
            self.on_trigger()
        finally:
            self._busy = False

    def _record_loop(self) -> None:
        import soundcard as sc
        mic = sc.default_microphone()
        with mic.recorder(samplerate=RATE, channels=1) as recorder:
            while self._running:
                data = recorder.record(numframes=CHUNK)
                self._audio_callback(data)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
