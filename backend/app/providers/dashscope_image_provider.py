from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from time import sleep
from typing import Any
from uuid import uuid4

import httpx

from app.config import settings
from app.providers.image_provider import GeneratedImageFile
from app.providers.mock_image_provider import MockImageProvider


class DashscopeImageProvider(MockImageProvider):
    name = "dashscope"
    capabilities = {"text_to_image", "image_to_image", "reference_image"}

    def __init__(self) -> None:
        self.api_key = settings.dashscope_api_key
        self.model = settings.dashscope_image_model
        self.base_url = self._base_api_url(settings.dashscope_image_generation_url)
        self.generation_url = f"{self.base_url}/services/aigc/image-generation/generation"
        self.poll_interval_seconds = 2
        self.max_poll_attempts = max(1, int(settings.model_request_timeout // self.poll_interval_seconds))

    def generate_images(self, **kwargs):
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required when IMAGE_PROVIDER=dashscope.")

        project_id = kwargs["project_id"]
        positive_prompt = kwargs["positive_prompt"]
        negative_prompt = kwargs["negative_prompt"]
        size = kwargs["size"]
        count = kwargs["count"]
        source_image_path = kwargs.get("source_image_path")

        project_dir = settings.generated_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        provider_size = self._dashscope_size(size)
        width, height = self._parse_size(size)
        image_urls: list[str] = []

        remaining = count
        while remaining > 0:
            batch_count = min(remaining, 4)
            image_urls.extend(
                self._request_image_urls(
                    positive_prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    size=provider_size,
                    count=batch_count,
                    source_image_path=source_image_path,
                )
            )
            remaining -= batch_count

        files: list[GeneratedImageFile] = []
        for index, image_url in enumerate(image_urls[:count]):
            target = project_dir / f"dashscope_{uuid4().hex}_{index + 1}.png"
            self._download_image(image_url, target)
            files.append(
                GeneratedImageFile(
                    image_path=target,
                    image_url=f"/uploads/generated/{project_id}/{target.name}",
                    width=width,
                    height=height,
                )
            )
        return files

    def _request_image_urls(
        self,
        *,
        positive_prompt: str,
        negative_prompt: str,
        size: str,
        count: int,
        source_image_path: str | None = None,
    ) -> list[str]:
        prompt_text = f"{positive_prompt}\n\nNegative constraints: {negative_prompt}"
        content = [{"text": prompt_text}]
        source_reference = self._source_image_reference(source_image_path)
        if source_reference:
            content.insert(0, {"image": source_reference})

        payload = {
            "model": self.model,
            "input": {"messages": [{"role": "user", "content": content}]},
            "parameters": {
                "enable_sequential": count > 1,
                "n": count,
                "size": size,
                "watermark": False,
            },
        }
        if not source_reference and count == 1:
            payload["parameters"]["thinking_mode"] = True

        task_id = self._create_task(payload)
        response = self._poll_task(task_id)

        images = self._extract_image_urls(response)
        if not images:
            raise RuntimeError(f"DashScope image response did not include generated image URLs: {response}")
        return images

    def _source_image_reference(self, source_image_path: str | None) -> str | None:
        if not source_image_path:
            return None
        path = Path(source_image_path)
        if not path.exists():
            return None
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type or not mime_type.startswith("image/"):
            raise RuntimeError(f"Unsupported source image type for DashScope: {path.name}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _base_api_url(self, value: str) -> str:
        url = value.rstrip("/")
        for suffix in (
            "/services/aigc/image-generation/generation",
            "/services/aigc/multimodal-generation/generation",
        ):
            if url.endswith(suffix):
                return url[: -len(suffix)]
        return url

    def _create_task(self, payload: dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        try:
            response = httpx.post(
                self.generation_url,
                headers=headers,
                json=payload,
                timeout=settings.model_request_timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"DashScope image task creation failed: {self._dashscope_error(exc.response)}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"DashScope image task creation failed: {exc}") from exc

        data = response.json()
        if self._get(data, "code"):
            raise RuntimeError(f"DashScope image task creation failed: {self._dashscope_error(data)}")
        task_id = self._get(self._get(data, "output", default={}), "task_id")
        if not task_id:
            raise RuntimeError(f"DashScope image task creation response did not include task_id: {data}")
        return str(task_id)

    def _poll_task(self, task_id: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/tasks/{task_id}"
        last_data: dict[str, Any] | None = None
        for _ in range(self.max_poll_attempts):
            try:
                response = httpx.get(url, headers=headers, timeout=settings.model_request_timeout)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(f"DashScope image task polling failed: {self._dashscope_error(exc.response)}") from exc
            except httpx.HTTPError as exc:
                raise RuntimeError(f"DashScope image task polling failed: {exc}") from exc

            data = response.json()
            last_data = data
            if self._get(data, "code"):
                raise RuntimeError(f"DashScope image task polling failed: {self._dashscope_error(data)}")

            output = self._get(data, "output", default={})
            status = str(self._get(output, "task_status", default="")).upper()
            if status == "SUCCEEDED":
                return data
            if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                message = self._get(data, "message") or self._get(output, "message") or status
                raise RuntimeError(f"DashScope image task {task_id} ended with {status}: {message}")
            sleep(self.poll_interval_seconds)

        raise RuntimeError(f"DashScope image task {task_id} did not finish before timeout: {last_data}")

    def _extract_image_urls(self, response: Any) -> list[str]:
        data = response if isinstance(response, dict) else getattr(response, "output", None)
        if self._get(data, "output") is not None:
            data = self._get(data, "output")
        images: list[str] = []

        results = self._get(data, "results", default=[])
        for item in results or []:
            url = self._get(item, "url") or self._get(item, "image") or self._get(item, "image_url")
            if url:
                images.append(str(url))

        choices = self._get(data, "choices", default=[])
        for choice in choices or []:
            content = self._get(self._get(choice, "message", default={}), "content", default=[])
            for item in content or []:
                url = self._get(item, "image") or self._get(item, "url") or self._get(item, "image_url")
                if url:
                    images.append(str(url))
        return images

    def _get(self, value: Any, key: str, default=None):
        if isinstance(value, dict):
            return value.get(key, default)
        return getattr(value, key, default)

    def _dashscope_error(self, value: Any) -> str:
        if isinstance(value, httpx.Response):
            try:
                value = value.json()
            except ValueError:
                return value.text
        code = self._get(value, "code")
        message = self._get(value, "message")
        request_id = self._get(value, "request_id")
        parts = [str(item) for item in [code, message, f"request_id={request_id}" if request_id else None] if item]
        return " | ".join(parts) or str(value)

    def _download_image(self, image_url: str, target) -> None:
        try:
            response = httpx.get(image_url, timeout=settings.model_request_timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to download DashScope image: {exc}") from exc
        target.write_bytes(response.content)

    def _dashscope_size(self, size: str) -> str:
        return "2K"
