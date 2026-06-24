from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings
from app.providers.text_provider import TextProviderError, TextProviderUnavailable


class DashscopeTextProvider:
    name = "dashscope"

    def __init__(self) -> None:
        self.api_key = settings.dashscope_api_key
        self.model = settings.text_model
        self.base_url = settings.dashscope_text_base_url.rstrip("/")

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise TextProviderUnavailable("DASHSCOPE_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n\n"
                        f"Return only valid JSON for the {schema_name} schema. "
                        "Do not wrap the JSON in Markdown."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=settings.model_request_timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise TextProviderError(f"DashScope text request failed: {exc}") from exc
        except ValueError as exc:
            raise TextProviderError("DashScope text response was not valid JSON.") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise TextProviderError("DashScope text response did not include message content.") from exc

        return self._parse_json_content(content)

    def _parse_json_content(self, content: Any) -> dict[str, Any]:
        if isinstance(content, list):
            content = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
        if not isinstance(content, str):
            raise TextProviderError("DashScope text content was not a string.")

        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TextProviderError("DashScope text content was not valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise TextProviderError("DashScope text content must be a JSON object.")
        return parsed
