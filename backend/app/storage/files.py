from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def save_upload_file(project_id: int, upload: UploadFile) -> tuple[str, str, str]:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("仅支持 JPG、PNG、WebP 格式")

    project_dir = settings.upload_dir / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{suffix}"
    target = project_dir / filename
    with target.open("wb") as file:
        while chunk := upload.file.read(1024 * 1024):
            file.write(chunk)
    return str(target), f"/uploads/{project_id}/{filename}", upload.content_type or suffix.lstrip(".")

