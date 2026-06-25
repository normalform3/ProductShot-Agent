from __future__ import annotations

from pathlib import Path
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
        self.generation_url = settings.dashscope_image_generation_url

    def generate_images(self, **kwargs):
        if not self.api_key:
            return super().generate_images(**kwargs)

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
        try:
            import dashscope
            from dashscope.aigc.image_generation import ImageGeneration
            from dashscope.api_entities.dashscope_response import Message
        except ImportError as exc:
            raise RuntimeError("dashscope package is not installed. Run `pip install -r requirements.txt`.") from exc

        dashscope.base_http_api_url = settings.dashscope_base_http_api_url
        prompt_text = f"{positive_prompt}\n\nNegative constraints: {negative_prompt}"
        content = [{"text": prompt_text}]
        source_reference = self._source_image_reference(source_image_path)
        if source_reference:
            content.insert(0, {"image": source_reference})
        message = Message(role="user", content=content)

        try:
            response = ImageGeneration.call(
                model=self.model,
                api_key=self.api_key,
                messages=[message],
                enable_sequential=count > 1,
                n=count,
                size=size,
            )
        except Exception as exc:
            raise RuntimeError(f"DashScope image SDK request failed: {exc}") from exc

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
        return path.resolve().as_uri()

    def _extract_image_urls(self, response: Any) -> list[str]:
        data = response if isinstance(response, dict) else getattr(response, "output", None)
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

    def _download_image(self, image_url: str, target) -> None:
        try:
            response = httpx.get(image_url, timeout=settings.model_request_timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to download DashScope image: {exc}") from exc
        target.write_bytes(response.content)

    def _dashscope_size(self, size: str) -> str:
        return "2K"
