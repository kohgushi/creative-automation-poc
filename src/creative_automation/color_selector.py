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
    """Raised when text color selection cannot complete safely."""

    pass


class ColorSelector(ABC):
    """Interface for choosing creative text colors before rendering."""

    @abstractmethod
    def select_colors(
        self,
        campaign: CampaignBrief,
        product: Product,
        source_visual_path: Path,
        template: AspectRatioTemplate,
    ) -> CreativeTextColors:
        """Choose text colors for a product variant.

        Args:
            campaign: Campaign context and brand colors.
            product: Product context used by AI-backed selectors.
            source_visual_path: Reference source visual for color analysis.
            template: Aspect-ratio template defining text safe areas.

        Returns:
            Colors for brand text, campaign message, and CTA.
        """
        pass


class RuleBasedColorSelector(ColorSelector):
    """Deterministic color selector used for tests and local development."""

    def select_colors(
        self,
        campaign: CampaignBrief,
        product: Product,
        source_visual_path: Path,
        template: AspectRatioTemplate,
    ) -> CreativeTextColors:
        """Choose high-contrast colors from simple image brightness analysis.

        Args:
            campaign: Campaign context and brand colors.
            product: Product context; unused by this deterministic selector.
            source_visual_path: Reference source visual for color analysis.
            template: Aspect-ratio template defining text safe areas.

        Returns:
            Selected colors with shared campaign message and CTA colors.
        """
        summary = summarize_template_regions(source_visual_path, template)
        campaign_color = _campaign_color_from_brightness(summary["message"]["brightness"])
        brand_color = select_brand_color(campaign, summary["logo"]["brightness"], fallback=campaign_color)
        return CreativeTextColors(brand=brand_color, campaign_message=campaign_color, cta=campaign_color)


class OpenAIColorSelector(ColorSelector):
    """OpenAI-backed selector for campaign message and CTA colors."""

    def __init__(self, settings: OpenAISettings | None = None) -> None:
        """Initialize the selector.

        Args:
            settings: Optional OpenAI settings. Defaults to environment-backed settings.
        """
        self.settings = settings or load_openai_settings()

    def select_colors(
        self,
        campaign: CampaignBrief,
        product: Product,
        source_visual_path: Path,
        template: AspectRatioTemplate,
    ) -> CreativeTextColors:
        """Use OpenAI and local contrast checks to select creative text colors.

        Args:
            campaign: Campaign context and brand colors.
            product: Product context included in the AI instruction.
            source_visual_path: Reference source visual for color analysis.
            template: Aspect-ratio template defining text safe areas.

        Returns:
            Selected colors with brand contrast computed locally.

        Raises:
            ColorSelectionError: If settings, OpenAI response, or color parsing fail.
        """
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
    """Create a color selector by provider name.

    Args:
        name: Selector provider name such as `rule-based` or `openai`.

    Returns:
        Color selector implementation.

    Raises:
        ColorSelectionError: If the provider name is unsupported.
    """
    normalized = name.strip().lower()
    if normalized in {"rule-based", "rule_based", "rules"}:
        return RuleBasedColorSelector()
    if normalized == "openai":
        return OpenAIColorSelector()
    raise ColorSelectionError(f"Unsupported color selector: {name}")


def summarize_template_regions(source_visual_path: Path, template: AspectRatioTemplate) -> dict[str, dict[str, object]]:
    """Summarize image brightness in text safe areas.

    Args:
        source_visual_path: Source visual to analyze.
        template: Renderer template with logo, message, and CTA boxes.

    Returns:
        Region summaries keyed by `logo`, `message`, and `cta`.
    """
    canvas = cover_image_for_template(source_visual_path, template).convert("RGB")
    return {
        "logo": _region_summary(template_region(canvas, template.logo_box)),
        "message": _region_summary(template_region(canvas, template.message_box)),
        "cta": _region_summary(template_region(canvas, template.cta_box)),
    }


def select_brand_color(campaign: CampaignBrief, background_brightness: float, fallback: str) -> str:
    """Choose the brand candidate color with highest contrast.

    Args:
        campaign: Campaign containing primary and secondary brand colors.
        background_brightness: Average brightness behind the logo safe area.
        fallback: Color used when no valid brand colors are configured.

    Returns:
        Selected hex color.
    """
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
    """Calculate compact color statistics for an image crop.

    Args:
        image: Cropped region to analyze.

    Returns:
        Average brightness and mean RGB values.
    """
    stat = ImageStat.Stat(image)
    mean = stat.mean[:3]
    brightness = sum(mean) / 3
    return {
        "brightness": round(brightness, 2),
        "mean_rgb": [round(channel, 2) for channel in mean],
    }


def _campaign_color_from_brightness(brightness: float) -> str:
    """Return a deterministic campaign text color for a brightness level.

    Args:
        brightness: Average background brightness from 0 to 255.

    Returns:
        Dark teal for bright backgrounds, otherwise white.
    """
    if brightness > 150:
        return DEFAULT_CAMPAIGN_TEXT_COLOR
    return "#FFFFFF"


def _validate_hex(value: object) -> str:
    """Validate and normalize an AI-selected hex color.

    Args:
        value: Candidate value returned by the AI selector.

    Returns:
        Uppercase `#RRGGBB` hex color.

    Raises:
        ColorSelectionError: If the value is not a valid hex color.
    """
    if not isinstance(value, str) or not HEX_COLOR_PATTERN.match(value):
        raise ColorSelectionError(f"Expected hex color, got {value!r}")
    return value.upper()


def _relative_luminance(hex_color: str) -> float:
    """Compute WCAG-style relative luminance for a hex color.

    Args:
        hex_color: Color in `#RRGGBB` format.

    Returns:
        Relative luminance between 0 and 1.
    """
    stripped = hex_color.lstrip("#")
    channels = [int(stripped[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(luminance_a: float, luminance_b: float) -> float:
    """Compute contrast ratio from two relative luminance values.

    Args:
        luminance_a: First relative luminance value.
        luminance_b: Second relative luminance value.

    Returns:
        Contrast ratio where higher values are more readable.
    """
    lighter = max(luminance_a, luminance_b)
    darker = min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


def _openai_color_instruction(
    campaign: CampaignBrief,
    product: Product,
    template: AspectRatioTemplate,
    summary: dict[str, dict[str, object]],
) -> str:
    """Build the OpenAI instruction for selecting campaign text color.

    Args:
        campaign: Campaign context.
        product: Product context.
        template: Reference renderer template.
        summary: Image region statistics used as visual context.

    Returns:
        Prompt requiring a JSON payload with one campaign message color.
    """
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
