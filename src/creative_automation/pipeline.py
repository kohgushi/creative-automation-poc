from __future__ import annotations

from pathlib import Path

from creative_automation.asset_store import AssetStore
from creative_automation.brief_loader import load_campaign_brief
from creative_automation.generators import get_image_generator
from creative_automation.models import AssetSource
from creative_automation.models import DryRunResult
from creative_automation.prompt_planner import get_prompt_planner


def build_dry_run_result(
    brief_path: Path | str,
    asset_root: Path | str,
    output_root: Path | str,
    prompt_planner_name: str | None = None,
    show_prompts: bool = False,
) -> DryRunResult:
    campaign = load_campaign_brief(brief_path)
    asset_store = AssetStore(asset_root=asset_root, output_root=output_root)
    products = asset_store.build_asset_plan(campaign)
    if show_prompts:
        planner = get_prompt_planner(prompt_planner_name or "rule-based")
        for product_plan in products:
            product_plan.prompts = [
                prompt
                for variant in product_plan.variants
                if (prompt := planner.plan_prompt(campaign, product_plan.product, variant)) is not None
            ]
    return DryRunResult(campaign=campaign, products=products)


def prepare_source_visuals(
    brief_path: Path | str,
    asset_root: Path | str,
    output_root: Path | str,
    prompt_planner_name: str,
    image_provider_name: str,
) -> DryRunResult:
    campaign = load_campaign_brief(brief_path)
    asset_store = AssetStore(asset_root=asset_root, output_root=output_root)
    products = asset_store.build_asset_plan(campaign)
    prompt_planner = get_prompt_planner(prompt_planner_name)
    image_generator = get_image_generator(image_provider_name)

    for product_plan in products:
        prompts = []
        for variant in product_plan.variants:
            variant_output_dir = asset_store.output_dir_for(campaign.campaign_id, variant)
            if variant.source == AssetSource.REUSED_SOURCE_VISUAL:
                variant.prepared_source_visual_path = variant.source_visual_path
                continue

            prompt = prompt_planner.plan_prompt(campaign, product_plan.product, variant)
            if prompt is None:
                continue
            prompts.append(prompt)
            generated_path = variant_output_dir / "generated_source_visual.png"
            image_generator.generate_source_visual(
                prompt=prompt.prompt,
                output_path=generated_path,
                product_asset_path=variant.product_asset_path,
            )
            variant.generated_source_visual_path = generated_path
            variant.prepared_source_visual_path = generated_path
        product_plan.prompts = prompts

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
            prepared_path = variant.prepared_source_visual_path.as_posix() if variant.prepared_source_visual_path else None
            suffix = f" prepared={prepared_path}" if prepared_path else ""
            lines.append(f"  - {variant.variant_id}: {variant.source.value} input={input_path}{suffix}")
        for prompt in product_plan.prompts:
            prompt_label = _prompt_label(prompt.prompt_type)
            lines.append(f"    prompt[{prompt.variant_id} {prompt_label}]: {prompt.prompt}")

    return "\n".join(lines)


def _prompt_label(source: AssetSource) -> str:
    if source == AssetSource.GENERATED_FROM_PRODUCT_ASSET:
        return "product-to-source-visual"
    if source == AssetSource.GENERATED_FROM_TEXT:
        return "text-to-source-visual"
    return source.value
