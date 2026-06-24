from app.providers.text_provider import TextProviderUnavailable


class MockTextProvider:
    name = "mock"
    model = "local-rules"

    def generate_json(self, **kwargs):
        raise TextProviderUnavailable("MockTextProvider does not call an external model.")
