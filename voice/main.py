import argparse
import os
import select
import signal
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

if os.name == "posix":
    import termios
    import tty
else:  # pragma: no cover - non-posix fallback
    termios = None
    tty = None
    import msvcrt

try:
    from colorama import Fore, Style, Back, init
    # Initialize colorama with strip=False to ensure colors work in all terminals
    init(autoreset=True, strip=False, convert=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Fallback no-op classes
    class Fore:
        CYAN = ""
        GREEN = ""
        YELLOW = ""
        RED = ""
        MAGENTA = ""
        BLUE = ""
    class Back:
        BLACK = ""
    class Style:
        RESET_ALL = ""
        BRIGHT = ""

from .audio import AudioRecorder
from .ollama_client import OllamaClient, Message
from .whisper_client import WhisperCppClient

BOX_WIDTH = 60  # width for content inside the chat boxes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Terminal voice agent (Ollama + whisper.cpp).")
    parser.add_argument("--model", default="llama3", help="Ollama model name.")
    parser.add_argument("--system", default="You are a concise assistant.", help="System prompt.")
    parser.add_argument("--whisper-binary", default="./whisper.cpp/build/bin/whisper-cli", help="Path to whisper.cpp binary.")
    parser.add_argument(
        "--whisper-model",
        default="./whisper.cpp/models/ggml-base.en.bin",
        help="Path to whisper.cpp model file.",
    )
    parser.add_argument("--threads", type=int, default=4, help="Threads for whisper.cpp.")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Microphone sample rate.")
    parser.add_argument("--channels", type=int, default=1, help="Microphone channel count.")
    parser.add_argument("--input-device", default=None, help="Sounddevice input device name or index.")
    parser.add_argument("--keep-recordings", action="store_true", help="Keep recorded wav files.")
    parser.add_argument("--record-dir", default=".voice-recordings", help="Directory to store recordings.")
    parser.add_argument("--max-history", type=int, default=10, help="Number of turns to keep for context.")
    parser.add_argument("--language", default=None, help="Force language code for whisper.cpp (e.g., en).")
    return parser.parse_args()


class TerminalController:
    """Handle raw terminal input for ctrl+T / ctrl+S bindings."""

    def __init__(self):
        self.is_windows = os.name != "posix"
        if not self.is_windows:
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
            # Try to prevent ctrl+S from pausing the terminal.
            try:
                subprocess.run(["stty", "-ixon"], check=False)
            except FileNotFoundError:
                pass

    def restore(self):
        if not self.is_windows:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def read_key(self, timeout: float = 0.1):
        if self.is_windows:
            # Windows implementation using msvcrt
            import time
            start = time.time()
            while time.time() - start < timeout:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    # Handle special keys
                    if ch == b'\x00' or ch == b'\xe0':  # Special key prefix
                        msvcrt.getch()  # Consume the actual key code
                        return None
                    # Return the raw byte value as a character with the ord value
                    # This allows us to check ord(key) for control characters
                    byte_val = ord(ch) if isinstance(ch, bytes) else ord(ch.encode())
                    return chr(byte_val)
                time.sleep(0.01)
            return None
        else:
            # POSIX implementation
            readable, _, _ = select.select([sys.stdin], [], [], timeout)
            if readable:
                return sys.stdin.read(1)
            return None


class VoiceAgent:
    def __init__(
        self,
        args: argparse.Namespace,
    ):
        record_dir = Path(args.record_dir)
        device = None
        if args.input_device is not None:
            device = int(args.input_device) if str(args.input_device).isdigit() else args.input_device

        self.recorder = AudioRecorder(
            sample_rate=args.sample_rate,
            channels=args.channels,
            output_dir=record_dir,
            device=device,
        )
        self.whisper = WhisperCppClient(
            binary=Path(args.whisper_binary),
            model=Path(args.whisper_model),
            threads=args.threads,
            language=args.language,
        )
        self.ollama = OllamaClient(model=args.model)
        self.system_prompt = args.system
        self.keep_recordings = args.keep_recordings
        self.max_history = args.max_history
        self.history: List[Message] = []

    def start(self):
        print("Voice agent ready.")
        print("Press Ctrl+T to start/stop recording. Press Ctrl+R to type a message. Press q to quit.")
        if os.name == "posix":
            print("Tip: If Ctrl+S freezes the terminal, run `stty -ixon` before starting.")
        controller = TerminalController()
        if os.name == "posix":
            signal.signal(signal.SIGINT, lambda sig, frame: self._graceful_exit(controller))

        try:
            while True:
                key = controller.read_key()
                if key is None:
                    continue

                code = ord(key)

                if code == 20:  # Ctrl+T - toggle recording
                    if self.recorder.is_recording:
                        self._handle_stop()
                    else:
                        self._handle_start()
                elif code == 18:  # Ctrl+R - text input mode
                    self._handle_text_input(controller)
                elif code == 19:  # Ctrl+S (for backwards compatibility on POSIX)
                    if self.recorder.is_recording:
                        self._handle_stop()
                elif key.lower() == "q":
                    print("Exiting.")
                    break
        finally:
            controller.restore()

    def _handle_text_input(self, controller: TerminalController):
        """Handle text input mode - restore terminal, get input, then restore raw mode."""
        try:
            # Restore terminal to normal mode for input
            controller.restore()

            # Print prompt
            print(f"\n{Style.BRIGHT}{Fore.MAGENTA}[Type your message, press Enter to send]{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}> {Style.RESET_ALL}", end="", flush=True)

            # Get user input
            user_input = input().strip()

            if not user_input:
                print(f"{Fore.YELLOW}[info] Empty message, cancelled.{Style.RESET_ALL}")
                return

            # Process the message
            self._print_user_message(user_input)

            try:
                reply = self._ask_ollama(user_input)
                self._print_bot_message(reply)
            except Exception as exc:
                print(f"{Fore.RED}[error] Ollama request failed: {exc}{Style.RESET_ALL}")

        finally:
            # Restore raw terminal mode for keyboard controls
            if os.name == "posix":
                import tty
                tty.setcbreak(controller.fd)
            # On Windows, msvcrt handles input differently, no restoration needed
            print()  # Add newline for clean display

    def _handle_start(self):
        try:
            self.recorder.start()
            print(f"{Fore.YELLOW}[rec] recording... (Ctrl+T to stop){Style.RESET_ALL}")
        except Exception as exc:  # pragma: no cover - interactive
            print(f"{Fore.RED}[error] failed to start recording: {exc}{Style.RESET_ALL}")

    def _handle_stop(self):
        if not self.recorder.is_recording:
            print(f"{Fore.YELLOW}[warn] Not recording.{Style.RESET_ALL}")
            return
        try:
            audio_path = self.recorder.stop(keep_file=self.keep_recordings)
            print(f"{Fore.YELLOW}[rec] saved audio: {audio_path}{Style.RESET_ALL}")
        except Exception as exc:  # pragma: no cover - interactive
            print(f"{Fore.RED}[error] failed to stop recording: {exc}{Style.RESET_ALL}")
            return

        try:
            transcript = self.whisper.transcribe(audio_path)
            self._print_user_message(transcript)
        except Exception as exc:  # pragma: no cover - interactive
            print(f"{Fore.RED}[error] transcription failed: {exc}{Style.RESET_ALL}")
            if audio_path.exists() and not self.keep_recordings:
                audio_path.unlink(missing_ok=True)
            return

        if audio_path.exists() and not self.keep_recordings:
            audio_path.unlink(missing_ok=True)

        try:
            reply = self._ask_ollama(transcript)
            self._print_bot_message(reply)
        except Exception as exc:  # pragma: no cover - interactive
            print(f"{Fore.RED}[error] Ollama request failed: {exc}{Style.RESET_ALL}")

    def _box_header(self, label: str, color) -> str:
        line_length = BOX_WIDTH + 4  # account for borders and spaces
        prefix = f"╭─ {label} "
        fill_len = max(line_length - len(prefix) - 1, 0)
        return f"{Style.BRIGHT}{color}{prefix}{'─' * fill_len}╮{Style.RESET_ALL}"

    def _box_footer(self, color) -> str:
        line_length = BOX_WIDTH + 4
        return f"{Style.BRIGHT}{color}╰{'─' * (line_length - 2)}╯{Style.RESET_ALL}"

    def _print_user_message(self, text: str):
        """Print user message with cyan styling and consistent box width."""
        print()
        print(self._box_header("YOU", Fore.CYAN))
        import textwrap

        payload = text.strip() or "(no transcription captured)"
        for line in payload.split('\n'):
            if line.strip():
                wrapped = textwrap.fill(line, width=BOX_WIDTH, subsequent_indent='  ')
                for wrapped_line in wrapped.split('\n'):
                    print(f"{Fore.CYAN}│ {wrapped_line:<{BOX_WIDTH}} │{Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}│ {'':<{BOX_WIDTH}} │{Style.RESET_ALL}")
        print(self._box_footer(Fore.CYAN))
        print()

    def _print_bot_message(self, text: str):
        """Print bot message with green styling and consistent box width."""
        print(self._box_header("ASSISTANT", Fore.GREEN))
        import textwrap

        lines = text.split('\n')
        if not any(line.strip() for line in lines):
            lines = ["(no response)"]

        for line in lines:
            if line.strip():
                leading_spaces = len(line) - len(line.lstrip())
                indent = ' ' * leading_spaces
                wrapped = textwrap.fill(
                    line.strip(),
                    width=BOX_WIDTH,
                    initial_indent=indent,
                    subsequent_indent=indent + '  ',
                )
                for wrapped_line in wrapped.split('\n'):
                    print(f"{Fore.GREEN}│ {wrapped_line:<{BOX_WIDTH}} │{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}│ {'':<{BOX_WIDTH}} │{Style.RESET_ALL}")
        print(self._box_footer(Fore.GREEN))
        print()

    def _ask_ollama(self, user_message: str) -> str:
        reply = self.ollama.generate(self.system_prompt, self.history, user_message)
        self.history.append(("user", user_message))
        self.history.append(("assistant", reply))
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2 :]
        return reply

    def _graceful_exit(self, controller: TerminalController):
        controller.restore()
        if self.recorder.is_recording:
            try:
                self.recorder.stop(keep_file=self.keep_recordings)
            except Exception:
                pass
        sys.exit(0)


def main():
    args = parse_args()
    agent = VoiceAgent(args)
    agent.start()


if __name__ == "__main__":
    main()
