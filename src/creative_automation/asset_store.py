from __future__ import annotations

from pathlib import Path

from creative_automation.models import AssetSource, AssetVariant, CampaignBrief, ProductAssetPlan

IMAGE_SUFFIXES = {".png"}


class AssetStore:
    """Discovers input assets and computes output paths for campaign runs."""

    def __init__(self, asset_root: Path | str, output_root: Path | str) -> None:
        """Initialize the asset store.

        Args:
            asset_root: Root directory containing `products/<product_id>/` assets.
            output_root: Root directory where generated outputs should be written.
        """
        self.asset_root = Path(asset_root)
        self.output_root = Path(output_root)

    def build_asset_plan(self, campaign: CampaignBrief) -> list[ProductAssetPlan]:
        """Build asset variants for every product in a campaign brief.

        Args:
            campaign: Validated campaign brief.

        Returns:
            Product-level asset plans with discovered source visuals or product assets.
        """
        return [
            ProductAssetPlan(product=product, variants=self.discover_product_variants(product.id))
            for product in campaign.products
        ]

    def discover_product_variants(self, product_id: str) -> list[AssetVariant]:
        """Discover reusable and generatable asset variants for one product.

        Args:
            product_id: Product identifier from the campaign brief.

        Returns:
            Asset variants ordered as reused source visuals, product assets, or a
            text-generated fallback when no local images exist.
        """
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
        """Return the output directory for a campaign/product/variant tuple.

        Args:
            campaign_id: Campaign identifier used as the output namespace.
            variant: Asset variant being rendered or generated.

        Returns:
            Directory path for all files produced for the variant.
        """
        return self.output_root / campaign_id / variant.product_id / variant.variant_id


def _image_files(directory: Path) -> list[Path]:
    """List supported image files in a directory.

    Args:
        directory: Directory to scan.

    Returns:
        Sorted PNG paths, excluding hidden files and missing directories.
    """
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and not path.name.startswith(".")
    )
