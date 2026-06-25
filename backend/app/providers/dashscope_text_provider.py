from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings
from app.providers.text_provider import TextProviderError, TextProviderUnavailable


class DashscopeTextProvider:
    name = "dashscope"

    def __init__(self) -> None:
        self.api_key = settings.dashscope_api_key
        self.model = settings.text_model
        self.base_url = settings.dashscope_base_http_api_url.rstrip("/")

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

        content = [
            {
                "text": (
                    f"{system_prompt}\n\n"
                    f"Return only valid JSON for the {schema_name} schema. Do not wrap the JSON in Markdown.\n\n"
                    f"User input:\n{user_prompt}"
                )
            }
        ]
        response = self._call_multimodal(content=content)
        return self._parse_json_content(self._response_text(response))

    def generate_multimodal_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_path: str,
        schema_name: str,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise TextProviderUnavailable("DASHSCOPE_API_KEY is not configured.")

        content = [
            {"image": self._image_reference(image_path)},
            {
                "text": (
                    f"{system_prompt}\n\n"
                    f"Return only valid JSON for the {schema_name} schema. Do not wrap the JSON in Markdown.\n\n"
                    f"User input:\n{user_prompt}"
                )
            },
        ]
        response = self._call_multimodal(content=content)
        return self._parse_json_content(self._response_text(response))

    def _call_multimodal(self, *, content: list[dict[str, str]]):
        try:
            import dashscope
        except ImportError as exc:
            raise TextProviderUnavailable("dashscope package is not installed. Run `pip install -r requirements.txt`.") from exc

        dashscope.base_http_api_url = self.base_url
        try:
            return dashscope.MultiModalConversation.call(
                api_key=self.api_key,
                model=self.model,
                messages=[{"role": "user", "content": content}],
            )
        except Exception as exc:
            raise TextProviderError(f"DashScope SDK request failed: {exc}") from exc

    def _response_text(self, response: Any) -> str:
        try:
            content = response.output.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise TextProviderError(f"DashScope SDK response did not include message content: {response}") from exc
        if isinstance(content, list):
            return "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content).strip()
        if isinstance(content, str):
            return content.strip()
        raise TextProviderError("DashScope SDK message content was not text.")

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

    def _image_reference(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise TextProviderError("DashScope multimodal image path does not exist.")
        return path.resolve().as_uri()
