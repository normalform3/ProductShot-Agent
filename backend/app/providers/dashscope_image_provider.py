from app.config import settings
from app.providers.mock_image_provider import MockImageProvider


class DashscopeImageProvider(MockImageProvider):
    name = "dashscope"

    def __init__(self) -> None:
        self.api_key = settings.dashscope_api_key

    def generate_images(self, **kwargs):
        if not self.api_key:
            return super().generate_images(**kwargs)
        raise NotImplementedError("DashscopeImageProvider is a scaffold. Use MockImageProvider for the MVP demo.")

