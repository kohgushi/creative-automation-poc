from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str | None
    text_model: str
    image_model: str


def load_openai_settings() -> OpenAISettings:
    load_dotenv()
    return OpenAISettings(
        api_key=os.getenv("OPENAI_API_KEY"),
        text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
        image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
    )
