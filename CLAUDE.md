Project goals for a terminal voice AI agent powered by local models (Ollama + whisper.cpp):

- Command-line first: run one CLI entry point to start a session, print bot replies inline, no extra UI.
- Voice loop: `Ctrl+T` begins recording; `Ctrl+S` ends recording, sends audio to whisper.cpp, and feeds the transcript to the bot. Make it easy to tweak the keybinds later.
- Conversation memory: keep a running chat history so the bot responses stay contextual inside the same session.
- Local models only: call Ollama for generation and whisper.cpp for ASR; avoid cloud dependencies.
- Robustness: handle missing model/audio deps gracefully, surface helpful errors, and never hang the terminal.
- Developer-friendly: simple setup steps (install, model pull, build), clear logs for each turn, and a small, readable codebase that can be extended with new commands.
