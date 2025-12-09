import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class WhisperCppClient:
    """Thin wrapper around whisper.cpp CLI."""

    def __init__(
        self,
        binary: Path,
        model: Path,
        threads: int = 4,
        language: Optional[str] = None,
        use_gpu: bool = True,
    ):
        self.binary = Path(binary)
        self.model = Path(model)
        self.threads = threads
        self.language = language
        self.use_gpu = use_gpu

    def transcribe(self, audio_path: Path) -> str:
        if not self.binary.exists():
            raise FileNotFoundError(f"whisper.cpp binary not found at {self.binary}")
        if not self.model.exists():
            raise FileNotFoundError(f"whisper.cpp model not found at {self.model}")
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file missing: {audio_path}")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".transcript")
        tmp.close()
        output_base = Path(tmp.name)
        txt_out = output_base.with_suffix(".txt")

        cmd = [
            str(self.binary),
            "-m",
            str(self.model),
            "-f",
            str(audio_path),
            "-otxt",
            "-of",
            str(output_base),
            "--no-prints",
            "--threads",
            str(self.threads),
        ]

        if self.language:
            cmd.extend(["-l", self.language])

        # Disable GPU if requested (GPU is enabled by default)
        if not self.use_gpu:
            cmd.append("--no-gpu")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            error_msg = f"whisper.cpp failed ({result.returncode})"
            if stderr:
                error_msg += f"\nSTDERR: {stderr}"
            if stdout:
                error_msg += f"\nSTDOUT: {stdout}"
            raise RuntimeError(error_msg)

        # Try to read from output file first
        if txt_out.exists():
            transcript = txt_out.read_text(encoding="utf-8").strip()
            txt_out.unlink(missing_ok=True)
            output_base.unlink(missing_ok=True)
            return transcript

        # Fallback: parse transcript from stdout
        # Format: [00:00:00.000 --> 00:00:04.000]   Text here
        stdout = result.stdout or ""
        import re
        # Extract text after timestamp markers
        matches = re.findall(r'\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]\s*(.+)', stdout)
        if matches:
            transcript = ' '.join(matches).strip()
            return transcript

        raise RuntimeError("whisper.cpp did not produce a transcript.")
