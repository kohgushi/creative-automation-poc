from __future__ import annotations

from pathlib import Path

from creative_automation.models import AssetSource, AssetVariant, CampaignBrief, ProductAssetPlan

IMAGE_SUFFIXES = {".png"}


class AssetStore:
    def __init__(self, asset_root: Path | str, output_root: Path | str) -> None:
        self.asset_root = Path(asset_root)
        self.output_root = Path(output_root)

    def build_asset_plan(self, campaign: CampaignBrief) -> list[ProductAssetPlan]:
        return [
            ProductAssetPlan(product=product, variants=self.discover_product_variants(product.id))
            for product in campaign.products
        ]

    def discover_product_variants(self, product_id: str) -> list[AssetVariant]:
        product_root = self.asset_root / "products" / product_id
        source_visuals = _image_files(product_root / "source_visuals")
        product_assets = _image_files(product_root / "product_assets")

        variants: list[AssetVariant] = []
        variants.extend(
            AssetVariant(
                product_id=product_id,
                variant_id=f"source_{path.stem}",
                source=AssetSource.REUSED_SOURCE_VISUAL,
                source_visual_path=path,
            )
            for path in source_visuals
        )
        variants.extend(
            AssetVariant(
                product_id=product_id,
                variant_id=f"product_{path.stem}",
                source=AssetSource.GENERATED_FROM_PRODUCT_ASSET,
                product_asset_path=path,
            )
            for path in product_assets
        )

        if not variants:
            variants.append(
                AssetVariant(
                    product_id=product_id,
                    variant_id="text_generated",
                    source=AssetSource.GENERATED_FROM_TEXT,
                )
            )

        return variants

    def output_dir_for(self, campaign_id: str, variant: AssetVariant) -> Path:
        return self.output_root / campaign_id / variant.product_id / variant.variant_id


def _image_files(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and not path.name.startswith(".")
    )
