from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AssetSource(StrEnum):
    """Origin type for an asset variant."""

    REUSED_SOURCE_VISUAL = "reused_source_visual"
    GENERATED_FROM_PRODUCT_ASSET = "generated_from_product_asset"
    GENERATED_FROM_TEXT = "generated_from_text"


class Brand(BaseModel):
    """Brand configuration from the campaign brief."""

    model_config = ConfigDict(extra="forbid")

    name: str
    primary_color: str | None = None
    secondary_color: str | None = None

    @field_validator("name")
    @classmethod
    def require_name(cls, value: str) -> str:
        """Validate that the brand name is present.

        Args:
            value: Raw brand name value.

        Returns:
            Cleaned brand name.
        """
        return _non_empty(value, "brand.name")


class Product(BaseModel):
    """Product entry from the campaign brief."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    visual_notes: str | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        """Validate a product identifier for path-safe usage.

        Args:
            value: Raw product identifier.

        Returns:
            Cleaned product identifier.
        """
        value = _non_empty(value, "product.id")
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("product.id must contain only letters, numbers, underscores, or hyphens")
        return value

    @field_validator("name")
    @classmethod
    def require_name(cls, value: str) -> str:
        """Validate that the product name is present.

        Args:
            value: Raw product name.

        Returns:
            Cleaned product name.
        """
        return _non_empty(value, "product.name")

    @field_validator("description")
    @classmethod
    def require_description(cls, value: str) -> str:
        """Validate that product description is present.

        Args:
            value: Raw product description.

        Returns:
            Cleaned product description.
        """
        return _non_empty(value, "product.description")


class CampaignBrief(BaseModel):
    """Validated campaign brief used by the pipeline."""

    model_config = ConfigDict(extra="forbid")

    campaign_id: str
    market: str
    target_audience: str
    campaign_message: str
    cta: str
    brand: Brand
    products: list[Product] = Field(min_length=2)
    campaign_name: str | None = None
    language: str = "en"
    locales: list[str] = Field(default_factory=lambda: ["en"], min_length=1)
    visual_direction: dict[str, Any] = Field(default_factory=dict)
    text_styles: dict[str, Any] = Field(default_factory=dict)

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, value: str) -> str:
        """Validate a campaign identifier for path-safe usage.

        Args:
            value: Raw campaign identifier.

        Returns:
            Cleaned campaign identifier.
        """
        value = _non_empty(value, "campaign_id")
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("campaign_id must contain only letters, numbers, underscores, or hyphens")
        return value

    @field_validator("market", "target_audience", "campaign_message", "cta")
    @classmethod
    def require_required_text(cls, value: str) -> str:
        """Validate required campaign text fields.

        Args:
            value: Raw text field value.

        Returns:
            Cleaned text value.
        """
        return _non_empty(value, "required text field")

    @field_validator("locales")
    @classmethod
    def validate_locales(cls, value: list[str]) -> list[str]:
        """Normalize and validate locale codes.

        Args:
            value: Raw locale list.

        Returns:
            Lowercase unique locale list.
        """
        normalized = []
        for locale in value:
            cleaned = _non_empty(locale, "locale").lower()
            if not cleaned.replace("-", "").isalnum():
                raise ValueError("locales must contain only letters, numbers, or hyphens")
            normalized.append(cleaned)
        if len(normalized) != len(set(normalized)):
            raise ValueError("locales must be unique")
        return normalized

    @model_validator(mode="after")
    def require_unique_product_ids(self) -> CampaignBrief:
        """Validate that product IDs are unique within the brief.

        Returns:
            Current campaign brief.
        """
        product_ids = [product.id for product in self.products]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("product ids must be unique")
        return self


class AssetVariant(BaseModel):
    """One source visual candidate for one product."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    product_id: str
    variant_id: str
    source: AssetSource
    source_visual_path: Path | None = None
    product_asset_path: Path | None = None
    prepared_source_visual_path: Path | None = None
    generated_source_visual_path: Path | None = None
    adapted_source_visual_paths: dict[str, Path] = Field(default_factory=dict)
    rendition_paths: list[Path] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @property
    def input_path(self) -> Path | None:
        """Return the local input asset path for this variant.

        Returns:
            Reused source visual path, product asset path, or `None`.
        """
        return self.source_visual_path or self.product_asset_path

    @property
    def final_source_visual_path(self) -> Path | None:
        """Return the source visual path that should be rendered.

        Returns:
            Prepared, reused, or generated source visual path.
        """
        return self.prepared_source_visual_path or self.source_visual_path or self.generated_source_visual_path


class PlannedPrompt(BaseModel):
    """Prompt planned for generating one source visual."""

    product_id: str
    variant_id: str
    prompt_type: AssetSource
    prompt: str


class LocalizedCreativeText(BaseModel):
    """Localized campaign message and CTA for one locale."""

    locale: str
    campaign_message: str
    cta: str


class CreativeTextColors(BaseModel):
    """Selected text colors for one asset variant."""

    brand: str
    campaign_message: str
    cta: str

    @field_validator("brand", "campaign_message", "cta")
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        """Validate a text color as `#RRGGBB`.

        Args:
            value: Raw color string.

        Returns:
            Validated color string.
        """
        value = _non_empty(value, "text color")
        if not value.startswith("#") or len(value) != 7:
            raise ValueError("text colors must use #RRGGBB hex format")
        try:
            int(value[1:], 16)
        except ValueError as exc:
            raise ValueError("text colors must use #RRGGBB hex format") from exc
        return value


class ProductAssetPlan(BaseModel):
    """Asset variants and prompts for one campaign product."""

    product: Product
    variants: list[AssetVariant]
    prompts: list[PlannedPrompt] = Field(default_factory=list)


class DryRunResult(BaseModel):
    """Pipeline result shared by dry-run and full execution paths."""

    campaign: CampaignBrief
    products: list[ProductAssetPlan]
    localized_texts: dict[str, LocalizedCreativeText] = Field(default_factory=dict)


def _non_empty(value: str, field_name: str) -> str:
    """Strip and validate a required string.

    Args:
        value: Raw string value.
        field_name: Human-readable field label for errors.

    Returns:
        Stripped string value.
    """
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value
