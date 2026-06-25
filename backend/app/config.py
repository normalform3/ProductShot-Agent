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
    text_provider = os.getenv("TEXT_PROVIDER", "mock").lower()
    text_model = os.getenv("TEXT_MODEL", "qwen3.7-plus")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    dashscope_workspace_id = os.getenv("DASHSCOPE_WORKSPACE_ID")
    dashscope_base_http_api_url = os.getenv(
        "DASHSCOPE_BASE_HTTP_API_URL",
        os.getenv("DASHSCOPE_TEXT_BASE_URL", "https://ws-k524juxb6rhpyhlp.cn-beijing.maas.aliyuncs.com/api/v1"),
    )
    dashscope_text_base_url = dashscope_base_http_api_url
    dashscope_image_model = os.getenv("DASHSCOPE_IMAGE_MODEL", "wan2.7-image-pro")
    dashscope_image_generation_url = dashscope_base_http_api_url
    model_request_timeout = float(os.getenv("MODEL_REQUEST_TIMEOUT", "180"))
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
