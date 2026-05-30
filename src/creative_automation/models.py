from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AssetSource(StrEnum):
    REUSED_SOURCE_VISUAL = "reused_source_visual"
    GENERATED_FROM_PRODUCT_ASSET = "generated_from_product_asset"
    GENERATED_FROM_TEXT = "generated_from_text"


class Brand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    primary_color: str | None = None
    secondary_color: str | None = None

    @field_validator("name")
    @classmethod
    def require_name(cls, value: str) -> str:
        return _non_empty(value, "brand.name")


class Product(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    visual_notes: str | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        value = _non_empty(value, "product.id")
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("product.id must contain only letters, numbers, underscores, or hyphens")
        return value

    @field_validator("name")
    @classmethod
    def require_name(cls, value: str) -> str:
        return _non_empty(value, "product.name")

    @field_validator("description")
    @classmethod
    def require_description(cls, value: str) -> str:
        return _non_empty(value, "product.description")


class CampaignBrief(BaseModel):
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
    visual_direction: dict[str, Any] = Field(default_factory=dict)
    text_styles: dict[str, Any] = Field(default_factory=dict)

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, value: str) -> str:
        value = _non_empty(value, "campaign_id")
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("campaign_id must contain only letters, numbers, underscores, or hyphens")
        return value

    @field_validator("market", "target_audience", "campaign_message", "cta")
    @classmethod
    def require_required_text(cls, value: str) -> str:
        return _non_empty(value, "required text field")

    @model_validator(mode="after")
    def require_unique_product_ids(self) -> CampaignBrief:
        product_ids = [product.id for product in self.products]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("product ids must be unique")
        return self


class AssetVariant(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    product_id: str
    variant_id: str
    source: AssetSource
    source_visual_path: Path | None = None
    product_asset_path: Path | None = None

    @property
    def input_path(self) -> Path | None:
        return self.source_visual_path or self.product_asset_path


class PlannedPrompt(BaseModel):
    product_id: str
    variant_id: str
    prompt_type: AssetSource
    prompt: str


class ProductAssetPlan(BaseModel):
    product: Product
    variants: list[AssetVariant]
    prompts: list[PlannedPrompt] = Field(default_factory=list)


class DryRunResult(BaseModel):
    campaign: CampaignBrief
    products: list[ProductAssetPlan]


def _non_empty(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value
