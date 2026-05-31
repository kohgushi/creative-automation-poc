from __future__ import annotations

import json
from abc import ABC, abstractmethod

from pydantic import ValidationError

from creative_automation.models import CampaignBrief, LocalizedCreativeText
from creative_automation.settings import OpenAISettings, SettingsError, load_openai_settings, validate_openai_settings


class LocalizationError(RuntimeError):
    pass


class Localizer(ABC):
    @abstractmethod
    def localize(self, campaign: CampaignBrief) -> dict[str, LocalizedCreativeText]:
        pass


class RuleBasedLocalizer(Localizer):
    def localize(self, campaign: CampaignBrief) -> dict[str, LocalizedCreativeText]:
        localized = {}
        for locale in campaign.locales:
            if locale == "en":
                localized[locale] = _source_text(campaign, locale)
            else:
                localized[locale] = LocalizedCreativeText(
                    locale=locale,
                    campaign_message=f"[{locale}] {campaign.campaign_message}",
                    cta=f"[{locale}] {campaign.cta}",
                )
        return localized


class OpenAILocalizer(Localizer):
    def __init__(self, settings: OpenAISettings | None = None) -> None:
        self.settings = settings or load_openai_settings()

    def localize(self, campaign: CampaignBrief) -> dict[str, LocalizedCreativeText]:
        localized = {}
        target_locales = []
        for locale in campaign.locales:
            if locale == "en":
                localized[locale] = _source_text(campaign, locale)
            else:
                target_locales.append(locale)

        if not target_locales:
            return localized

        try:
            validate_openai_settings(self.settings)
        except SettingsError as exc:
            raise LocalizationError(str(exc)) from exc

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LocalizationError("The openai package is required for --localizer openai") from exc

        client = OpenAI(api_key=self.settings.api_key)
        try:
            response = client.responses.create(
                model=self.settings.text_model,
                input=_localization_instruction(campaign, target_locales),
            )
        except Exception as exc:
            raise LocalizationError(f"OpenAI localization request failed: {exc}") from exc

        text = getattr(response, "output_text", None)
        if not text:
            raise LocalizationError("OpenAI localizer returned no text")

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LocalizationError(f"OpenAI localizer returned invalid JSON: {text}") from exc

        try:
            for locale in target_locales:
                entry = payload[locale]
                localized[locale] = LocalizedCreativeText(
                    locale=locale,
                    campaign_message=entry["campaign_message"],
                    cta=entry["cta"],
                )
        except (KeyError, TypeError, ValidationError) as exc:
            raise LocalizationError(f"OpenAI localizer returned an unexpected payload: {payload}") from exc

        return localized


def get_localizer(name: str) -> Localizer:
    normalized = name.strip().lower()
    if normalized == "rule-based":
        return RuleBasedLocalizer()
    if normalized == "openai":
        return OpenAILocalizer()
    raise LocalizationError(f"Unsupported localizer: {name}")


def _source_text(campaign: CampaignBrief, locale: str) -> LocalizedCreativeText:
    return LocalizedCreativeText(locale=locale, campaign_message=campaign.campaign_message, cta=campaign.cta)


def _localization_instruction(campaign: CampaignBrief, target_locales: list[str]) -> str:
    return (
        "You are a marketing localization specialist. Localize the campaign message and CTA from English "
        "for each requested locale. Keep the message concise enough for social ad image overlays. Preserve "
        "the marketing intent, avoid adding unsupported claims, and return only valid JSON with one object "
        "per locale. Each locale object must contain campaign_message and cta strings.\n\n"
        f"Brand: {campaign.brand.name}\n"
        f"Market: {campaign.market}\n"
        f"Target audience: {campaign.target_audience}\n"
        f"Source campaign message: {campaign.campaign_message}\n"
        f"Source CTA: {campaign.cta}\n"
        f"Target locales: {', '.join(target_locales)}\n"
        "Output example shape: {\"ja\": {\"campaign_message\": \"...\", \"cta\": \"...\"}}"
    )
