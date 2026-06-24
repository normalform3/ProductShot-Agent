from app.config import settings
from app.providers.dashscope_image_provider import DashscopeImageProvider
from app.providers.mock_image_provider import MockImageProvider
from app.providers.openai_image_provider import OpenAIImageProvider


def get_image_provider():
    if settings.image_provider == "openai":
        return OpenAIImageProvider()
    if settings.image_provider == "dashscope":
        return DashscopeImageProvider()
    return MockImageProvider()

