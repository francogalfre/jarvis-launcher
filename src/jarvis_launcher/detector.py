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
    def __init__(self, config: dict, on_trigger, on_audio_level=None, on_clap=None) -> None:
        self.config = config
        self.on_trigger = on_trigger
        self.on_audio_level = on_audio_level  # callback(level: float)
        self.on_clap = on_clap  # callback(count: int)
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

    def _audio_callback(self, audio: np.ndarray) -> None:
        """Process audio data. audio can be 1D or 2D."""
        if self._busy:
            return
        
        # Handle both 1D and 2D arrays
        if audio.ndim == 2:
            audio = audio[:, 0]
        
        audio = audio.astype(np.float32)
        detected, rms = self._is_clap(audio)
        
        # Debug: print audio level
        # print(f"DEBUG: rms={rms:.3f}, detected={detected}")
        
        # Send audio level to callback (normalized 0-1)
        if self.on_audio_level:
            threshold = self._adaptive_threshold()
            normalized = min(1.0, rms / (threshold * 2))
            self.on_audio_level(normalized)
        
        if detected:
            now = time.time()
            min_gap = self.config["min_seconds_between_claps"]
            if now - self.last_clap_time > min_gap:
                self.claps_detected += 1
                self.last_clap_time = now
                # Notify clap detection
                if self.on_clap:
                    self.on_clap(self.claps_detected)
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
        import miniaudio
        import queue as q

        audio_q: q.Queue = q.Queue(maxsize=50)

        # Generator that receives audio chunks from miniaudio
        def audio_gen():
            while self._running:
                # Prime: yield None initially, then receive chunks via send()
                chunk = yield
                if chunk:
                    try:
                        audio_q.put_nowait(bytes(chunk))
                    except q.Full:
                        pass

        gen = audio_gen()
        next(gen)  # Prime the generator before passing to miniaudio

        try:
            device = miniaudio.CaptureDevice(
                input_format=miniaudio.SampleFormat.FLOAT32,
                nchannels=1,
                sample_rate=RATE,
                buffersize_msec=50,
            )
            device.start(gen)
            
            while self._running:
                try:
                    raw = audio_q.get(timeout=0.2)
                    arr = np.frombuffer(raw, dtype=np.float32).reshape(-1, 1)
                    self._audio_callback(arr)
                except q.Empty:
                    # Send empty signal to keep generator alive
                    try:
                        gen.send(None)
                    except StopIteration:
                        break
                    continue
        except Exception as e:
            print(f"❌ Microphone error: {e}")
        finally:
            try:
                device.close()
            except Exception:
                pass

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
