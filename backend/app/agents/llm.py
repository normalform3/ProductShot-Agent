from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.providers import TextProvider
from app.providers.text_provider import TextProviderUnavailable

PayloadT = TypeVar("PayloadT", bound=BaseModel)


def generate_payload(
    *,
    provider: TextProvider,
    payload_type: type[PayloadT],
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    temperature: float = 0.4,
) -> PayloadT | None:
    try:
        data = provider.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_name=schema_name,
            temperature=temperature,
        )
    except TextProviderUnavailable:
        return None
    return payload_type.model_validate(data)
