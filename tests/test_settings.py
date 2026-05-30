from creative_automation.settings import OpenAISettings, SettingsError, validate_openai_settings

import pytest


def test_validate_openai_settings_requires_api_key() -> None:
    settings = OpenAISettings(api_key=None, text_model="gpt-4.1-mini", image_model="gpt-image-1")

    with pytest.raises(SettingsError, match="OPENAI_API_KEY"):
        validate_openai_settings(settings)


def test_validate_openai_settings_requires_image_model_when_requested() -> None:
    settings = OpenAISettings(api_key="test", text_model="gpt-4.1-mini", image_model="")

    with pytest.raises(SettingsError, match="OPENAI_IMAGE_MODEL"):
        validate_openai_settings(settings, require_image_model=True)


def test_validate_openai_settings_accepts_complete_settings() -> None:
    settings = OpenAISettings(api_key="test", text_model="gpt-4.1-mini", image_model="gpt-image-1")

    validate_openai_settings(settings, require_image_model=True)
