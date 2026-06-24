from pathlib import Path
import os


class Settings:
    app_name = "ProductShot Agent"
    api_prefix = "/api"
    backend_dir = Path(__file__).resolve().parents[1]
    data_dir = backend_dir / "data"
    upload_dir = backend_dir / "uploads"
    generated_dir = upload_dir / "generated"
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{data_dir / 'productshot.db'}")
    image_provider = os.getenv("IMAGE_PROVIDER", "mock").lower()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
        if origin.strip()
    ]

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()

