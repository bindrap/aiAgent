import subprocess
from typing import List, Tuple


Message = Tuple[str, str]  # (role, content)


class OllamaClient:
    """Call Ollama via CLI."""

    def __init__(self, model: str = "llama3", timeout: int = 120):
        self.model = model
        self.timeout = timeout

    def generate(self, system_prompt: str, history: List[Message], user_message: str) -> str:
        prompt = self._format_prompt(system_prompt, history, user_message)
        result = subprocess.run(
            ["ollama", "run", self.model],
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=self.timeout,
        )

        if result.returncode != 0:
            stderr = (result.stderr or b"").decode("utf-8", errors="ignore").strip()
            raise RuntimeError(f"Ollama failed ({result.returncode}): {stderr}")

        return result.stdout.decode("utf-8", errors="ignore").strip()

    def _format_prompt(self, system_prompt: str, history: List[Message], user_message: str) -> str:
        lines = []
        if system_prompt:
            lines.append(f"System: {system_prompt}")
        for role, content in history:
            prefix = "User" if role == "user" else "Assistant"
            lines.append(f"{prefix}: {content}")
        lines.append(f"User: {user_message}")
        lines.append("Assistant:")
        return "\n".join(lines)
