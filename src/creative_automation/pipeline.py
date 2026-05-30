from __future__ import annotations

from pathlib import Path

from creative_automation.asset_store import AssetStore
from creative_automation.brief_loader import load_campaign_brief
from creative_automation.models import DryRunResult


def build_dry_run_result(brief_path: Path | str, asset_root: Path | str, output_root: Path | str) -> DryRunResult:
    campaign = load_campaign_brief(brief_path)
    asset_store = AssetStore(asset_root=asset_root, output_root=output_root)
    products = asset_store.build_asset_plan(campaign)
    return DryRunResult(campaign=campaign, products=products)


def format_dry_run(result: DryRunResult, output_root: Path | str) -> str:
    lines = [
        f"Campaign: {result.campaign.campaign_id}",
        f"Products: {len(result.products)}",
        f"Output root: {Path(output_root)}",
    ]

    for product_plan in result.products:
        lines.append(f"- {product_plan.product.id}: {product_plan.product.name}")
        for variant in product_plan.variants:
            input_path = variant.input_path.as_posix() if variant.input_path else "(none)"
            lines.append(f"  - {variant.variant_id}: {variant.source.value} input={input_path}")

    return "\n".join(lines)
