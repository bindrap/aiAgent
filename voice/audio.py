import queue
import tempfile
import threading
from pathlib import Path
from typing import Optional


class AudioRecorder:
    """Minimal audio recorder using sounddevice."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        output_dir: Optional[Path] = None,
        device: Optional[int | str] = None,
    ):
        try:
            import sounddevice as sd  # type: ignore
            import soundfile as sf  # type: ignore
            import numpy as np  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Missing audio deps. Install with `pip install sounddevice soundfile numpy`."
            ) from exc

        self.sd = sd
        self.sf = sf
        self.np = np
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir())
        self._queue: "queue.Queue" = queue.Queue()
        self._stream = None
        self._lock = threading.Lock()
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        with self._lock:
            if self._recording:
                raise RuntimeError("Recorder already running.")
            self._queue = queue.Queue()
            # Validate device early if provided.
            if self.device is not None:
                self.sd.query_devices(self.device, "input")
            self._stream = self.sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                callback=self._on_audio,
            )
            self._stream.start()
            self._recording = True

    def stop(self, keep_file: bool = False) -> Path:
        with self._lock:
            if not self._recording or not self._stream:
                raise RuntimeError("Recorder not running.")
            self._stream.stop()
            self._stream.close()
            self._stream = None
            self._recording = False

        frames = []
        while not self._queue.empty():
            frames.append(self._queue.get())

        if not frames:
            raise RuntimeError("No audio captured.")

        audio = self.np.concatenate(frames, axis=0)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        suffix = ".wav" if keep_file else ".tmp.wav"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=self.output_dir)
        tmp.close()
        file_path = Path(tmp.name)
        self.sf.write(file_path, audio, self.sample_rate)
        return file_path

    def _on_audio(self, indata, frames, time, status):  # pragma: no cover - sd callback
        if status:
            # Avoid noisy callbacks, but keep collecting audio.
            print(f"[warn] audio callback status: {status}")
        self._queue.put(indata.copy())
