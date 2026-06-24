from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class GeneratedImageFile:
    image_path: Path
    image_url: str
    width: int | None
    height: int | None


class ImageProvider(Protocol):
    name: str

    def generate_images(
        self,
        *,
        project_id: int,
        source_image_path: str | None,
        positive_prompt: str,
        negative_prompt: str,
        size: str,
        count: int,
    ) -> list[GeneratedImageFile]:
        ...
