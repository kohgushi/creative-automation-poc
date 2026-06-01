from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class OpenAISettings:
    """OpenAI credentials and model names loaded from the environment."""

    api_key: str | None
    text_model: str
    image_model: str


class SettingsError(RuntimeError):
    """Raised when required runtime settings are missing."""

    pass


def load_openai_settings() -> OpenAISettings:
    """Load OpenAI settings from `.env` and environment variables.

    Returns:
        OpenAI settings with default text and image model names.
    """
    load_dotenv()
    return OpenAISettings(
        api_key=os.getenv("OPENAI_API_KEY"),
        text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
        image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
    )


def validate_openai_settings(settings: OpenAISettings, require_image_model: bool = False) -> None:
    """Validate OpenAI settings for the requested provider operation.

    Args:
        settings: OpenAI settings to validate.
        require_image_model: Whether an image model name is required.

    Raises:
        SettingsError: If required credentials or model names are missing.
    """
    if not settings.api_key:
        raise SettingsError("OPENAI_API_KEY is required for OpenAI-backed execution")
    if not settings.text_model:
        raise SettingsError("OPENAI_TEXT_MODEL is required for OpenAI-backed prompt planning")
    if require_image_model and not settings.image_model:
        raise SettingsError("OPENAI_IMAGE_MODEL is required for OpenAI-backed image generation")
