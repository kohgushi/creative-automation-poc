from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image, ImageStat
from pydantic import ValidationError

from creative_automation.models import CampaignBrief, CreativeTextColors, Product
from creative_automation.renderer import AspectRatioTemplate, cover_image_for_template, template_region
from creative_automation.settings import OpenAISettings, SettingsError, load_openai_settings, validate_openai_settings


HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_CAMPAIGN_TEXT_COLOR = "#00687D"


class ColorSelectionError(RuntimeError):
    pass


class ColorSelector(ABC):
    @abstractmethod
    def select_colors(
        self,
        campaign: CampaignBrief,
        product: Product,
        source_visual_path: Path,
        template: AspectRatioTemplate,
    ) -> CreativeTextColors:
        pass


class RuleBasedColorSelector(ColorSelector):
    def select_colors(
        self,
        campaign: CampaignBrief,
        product: Product,
        source_visual_path: Path,
        template: AspectRatioTemplate,
    ) -> CreativeTextColors:
        summary = summarize_template_regions(source_visual_path, template)
        campaign_color = _campaign_color_from_brightness(summary["message"]["brightness"])
        brand_color = select_brand_color(campaign, summary["logo"]["brightness"], fallback=campaign_color)
        return CreativeTextColors(brand=brand_color, campaign_message=campaign_color, cta=campaign_color)


class OpenAIColorSelector(ColorSelector):
    def __init__(self, settings: OpenAISettings | None = None) -> None:
        self.settings = settings or load_openai_settings()

    def select_colors(
        self,
        campaign: CampaignBrief,
        product: Product,
        source_visual_path: Path,
        template: AspectRatioTemplate,
    ) -> CreativeTextColors:
        try:
            validate_openai_settings(self.settings)
        except SettingsError as exc:
            raise ColorSelectionError(str(exc)) from exc

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ColorSelectionError("The openai package is required for --color-selector openai") from exc

        summary = summarize_template_regions(source_visual_path, template)
        client = OpenAI(api_key=self.settings.api_key)
        try:
            response = client.responses.create(
                model=self.settings.text_model,
                input=_openai_color_instruction(campaign, product, template, summary),
            )
        except Exception as exc:
            raise ColorSelectionError(f"OpenAI color selector request failed: {exc}") from exc

        text = getattr(response, "output_text", None)
        if not text:
            raise ColorSelectionError("OpenAI color selector returned no text")

        try:
            payload = json.loads(text)
            campaign_color = _validate_hex(payload["campaign_message"])
        except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
            raise ColorSelectionError(f"OpenAI color selector returned an unexpected payload: {text}") from exc

        brand_color = select_brand_color(campaign, summary["logo"]["brightness"], fallback=campaign_color)
        return CreativeTextColors(brand=brand_color, campaign_message=campaign_color, cta=campaign_color)


def get_color_selector(name: str) -> ColorSelector:
    normalized = name.strip().lower()
    if normalized in {"rule-based", "rule_based", "rules"}:
        return RuleBasedColorSelector()
    if normalized == "openai":
        return OpenAIColorSelector()
    raise ColorSelectionError(f"Unsupported color selector: {name}")


def summarize_template_regions(source_visual_path: Path, template: AspectRatioTemplate) -> dict[str, dict[str, object]]:
    canvas = cover_image_for_template(source_visual_path, template).convert("RGB")
    return {
        "logo": _region_summary(template_region(canvas, template.logo_box)),
        "message": _region_summary(template_region(canvas, template.message_box)),
        "cta": _region_summary(template_region(canvas, template.cta_box)),
    }


def select_brand_color(campaign: CampaignBrief, background_brightness: float, fallback: str) -> str:
    candidates = [
        color
        for color in (campaign.brand.primary_color, campaign.brand.secondary_color)
        if color and HEX_COLOR_PATTERN.match(color)
    ]
    if not candidates:
        return fallback
    if len(candidates) == 1:
        return candidates[0]
    return max(candidates, key=lambda color: _contrast_ratio(_relative_luminance(color), background_brightness / 255))


def _region_summary(image: Image.Image) -> dict[str, object]:
    stat = ImageStat.Stat(image)
    mean = stat.mean[:3]
    brightness = sum(mean) / 3
    return {
        "brightness": round(brightness, 2),
        "mean_rgb": [round(channel, 2) for channel in mean],
    }


def _campaign_color_from_brightness(brightness: float) -> str:
    if brightness > 150:
        return DEFAULT_CAMPAIGN_TEXT_COLOR
    return "#FFFFFF"


def _validate_hex(value: object) -> str:
    if not isinstance(value, str) or not HEX_COLOR_PATTERN.match(value):
        raise ColorSelectionError(f"Expected hex color, got {value!r}")
    return value.upper()


def _relative_luminance(hex_color: str) -> float:
    stripped = hex_color.lstrip("#")
    channels = [int(stripped[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(luminance_a: float, luminance_b: float) -> float:
    lighter = max(luminance_a, luminance_b)
    darker = min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


def _openai_color_instruction(
    campaign: CampaignBrief,
    product: Product,
    template: AspectRatioTemplate,
    summary: dict[str, dict[str, object]],
) -> str:
    return (
        "You are choosing text colors for a social ad creative. Return only valid JSON. "
        "Choose one campaign message color that will also be used for the CTA button fill. "
        "Text visibility is the top priority. The color should feel fresh and suitable for the product and campaign. "
        "Avoid colors that blend into the source visual. Return a single hex color in the shape "
        "{\"campaign_message\":\"#RRGGBB\"}.\n\n"
        f"Brand: {campaign.brand.name}\n"
        f"Market: {campaign.market}\n"
        f"Target audience: {campaign.target_audience}\n"
        f"Campaign message: {campaign.campaign_message}\n"
        f"CTA: {campaign.cta}\n"
        f"Product: {product.name}\n"
        f"Product description: {product.description}\n"
        f"Product visual notes: {product.visual_notes or 'None'}\n"
        f"Aspect ratio: {template.ratio}\n"
        f"Source visual region summary: {json.dumps(summary)}"
    )
