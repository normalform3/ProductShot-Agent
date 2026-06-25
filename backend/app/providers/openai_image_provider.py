from app.config import settings
from app.providers.mock_image_provider import MockImageProvider


class OpenAIImageProvider(MockImageProvider):
    name = "openai"
    capabilities = {"text_to_image", "image_to_image", "reference_image"}

    def __init__(self) -> None:
        self.api_key = settings.openai_api_key

    def generate_images(self, **kwargs):
        if not self.api_key:
            return super().generate_images(**kwargs)
        raise NotImplementedError("OpenAIImageProvider is a scaffold. Use MockImageProvider for the MVP demo.")
