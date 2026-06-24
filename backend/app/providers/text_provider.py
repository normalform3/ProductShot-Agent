from __future__ import annotations

from typing import Any, Protocol


class TextProviderError(RuntimeError):
    """Raised when a configured text provider cannot complete a request."""


class TextProviderUnavailable(TextProviderError):
    """Raised when a text provider is intentionally unavailable."""


class TextProvider(Protocol):
    name: str
    model: str

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        ...
