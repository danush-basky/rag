from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


class PromptStore:
    """In-memory prompt text, loaded from and written back to the configured files."""

    def __init__(self) -> None:
        self.system_prompt = self._read(settings.JEE_SYSTEM_PROMPT_PATH)
        self.context_prompt = self._read(settings.JEE_CONTEXT_PROMPT_PATH)

    @staticmethod
    def _read(path: str) -> str:
        file = Path(path)
        if not file.exists():
            raise FileNotFoundError(f"Prompt file not found at: {file.resolve()}")
        return file.read_text(encoding="utf-8").strip()

    @staticmethod
    def _write(path: str, content: str) -> None:
        Path(path).write_text(content + "\n", encoding="utf-8")

    def update(
        self, system_prompt: str | None = None, context_prompt: str | None = None
    ) -> None:
        next_system = self.system_prompt
        next_context = self.context_prompt

        if system_prompt is not None:
            next_system = system_prompt.strip()
            if not next_system:
                raise ValueError("system_prompt cannot be empty")

        if context_prompt is not None:
            next_context = context_prompt.strip()
            if not next_context:
                raise ValueError("context_prompt cannot be empty")
            if "{exam}" not in next_context:
                raise ValueError("context_prompt must contain {exam}")

        if system_prompt is not None:
            self._write(settings.JEE_SYSTEM_PROMPT_PATH, next_system)
            self.system_prompt = next_system
        if context_prompt is not None:
            self._write(settings.JEE_CONTEXT_PROMPT_PATH, next_context)
            self.context_prompt = next_context


prompt_store = PromptStore()
