from __future__ import annotations

from uuid import uuid4

import httpx

from app.config import settings
from app.providers.image_provider import GeneratedImageFile
from app.providers.mock_image_provider import MockImageProvider


class DashscopeImageProvider(MockImageProvider):
    name = "dashscope"

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

        project_dir = settings.generated_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        provider_size = self._dashscope_size(size)
        width, height = self._parse_provider_size(provider_size)
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
    ) -> list[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if settings.dashscope_workspace_id:
            headers["X-DashScope-WorkSpace"] = settings.dashscope_workspace_id
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": positive_prompt}],
                    }
                ]
            },
            "parameters": {
                "prompt_extend": True,
                "watermark": False,
                "n": count,
                "negative_prompt": negative_prompt,
                "size": size,
            },
        }

        try:
            response = httpx.post(
                self.generation_url,
                headers=headers,
                json=payload,
                timeout=settings.model_request_timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"DashScope image request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("DashScope image response was not valid JSON.") from exc

        if data.get("code"):
            raise RuntimeError(f"DashScope image request failed: {data.get('message', data['code'])}")

        images: list[str] = []
        choices = data.get("output", {}).get("choices", [])
        for choice in choices:
            content = choice.get("message", {}).get("content", [])
            for item in content:
                image = item.get("image") if isinstance(item, dict) else None
                if image:
                    images.append(image)
        if not images:
            raise RuntimeError("DashScope image response did not include generated image URLs.")
        return images

    def _download_image(self, image_url: str, target) -> None:
        try:
            response = httpx.get(image_url, timeout=settings.model_request_timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to download DashScope image: {exc}") from exc
        target.write_bytes(response.content)

    def _dashscope_size(self, size: str) -> str:
        width, height = self._parse_size(size)
        ratio = width / height if height else 1
        if 0.95 <= ratio <= 1.05:
            return "1280*1280"
        if ratio < 0.62:
            return "960*1696"
        if ratio < 0.9:
            return "1104*1472"
        if ratio > 1.6:
            return "1696*960"
        return "1472*1104" if ratio > 1 else "1104*1472"

    def _parse_provider_size(self, size: str) -> tuple[int, int]:
        left, right = size.split("*", 1)
        return int(left), int(right)
