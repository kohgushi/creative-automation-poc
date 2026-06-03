from __future__ import annotations

from pathlib import Path

from creative_automation.asset_store import AssetStore
from creative_automation.brief_loader import load_campaign_brief
from creative_automation.color_selector import get_color_selector
from creative_automation.generators import get_image_generator
from creative_automation.localization import get_localizer
from creative_automation.models import AssetSource
from creative_automation.models import DryRunResult
from creative_automation.prompt_planner import get_prompt_planner
from creative_automation.renderer import CreativeRenderer, adaptation_specs, template_for_ratio


def build_dry_run_result(
    brief_path: Path | str,
    asset_root: Path | str,
    output_root: Path | str,
    prompt_planner_name: str | None = None,
    show_prompts: bool = False,
) -> DryRunResult:
    """Load inputs and classify assets without rendering final creatives.

    Args:
        brief_path: Campaign brief YAML path.
        asset_root: Local input asset root.
        output_root: Output root used for path planning.
        prompt_planner_name: Optional planner provider used when `show_prompts` is true.
        show_prompts: Whether to include generation prompts in the dry-run result.

    Returns:
        Pipeline result containing campaign and planned product asset variants.
    """
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
    """Prepare reusable or generated source visuals for all product variants.

    Args:
        brief_path: Campaign brief YAML path.
        asset_root: Local input asset root.
        output_root: Root directory for generated source visuals.
        prompt_planner_name: Prompt planner provider name.
        image_provider_name: Image generator provider name.

    Returns:
        Pipeline result with prepared source visual paths and generation prompts.
    """
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


def run_pipeline(
    brief_path: Path | str,
    asset_root: Path | str,
    output_root: Path | str,
    prompt_planner_name: str,
    image_provider_name: str,
    localizer_name: str = "openai",
    color_selector_name: str = "rule-based",
    adapt_source_visuals: bool = False,
) -> DryRunResult:
    """Run the full creative automation pipeline.

    Args:
        brief_path: Campaign brief YAML path.
        asset_root: Local input asset root.
        output_root: Root directory for generated outputs.
        prompt_planner_name: Prompt planner provider name.
        image_provider_name: Image generator provider name.
        localizer_name: Localization provider name.
        color_selector_name: Text color selector provider name.
        adapt_source_visuals: Whether to generate aspect-specific source visuals before rendering.

    Returns:
        Pipeline result with localized text, generated source visuals, and final renditions.
    """
    # 1. Resolve each product into reusable or generated source visuals.
    result = prepare_source_visuals(
        brief_path=brief_path,
        asset_root=asset_root,
        output_root=output_root,
        prompt_planner_name=prompt_planner_name,
        image_provider_name=image_provider_name,
    )
    asset_store = AssetStore(asset_root=asset_root, output_root=output_root)
    renderer = CreativeRenderer()
    image_generator = get_image_generator(image_provider_name)
    color_selector = get_color_selector(color_selector_name)

    # 2. Prepare localized campaign copy once, then reuse it across every rendered variant.
    result.localized_texts = get_localizer(localizer_name).localize(result.campaign)

    for product_plan in result.products:
        for variant in product_plan.variants:
            source_visual_path = variant.final_source_visual_path
            if source_visual_path is None:
                continue
            output_dir = asset_store.output_dir_for(result.campaign.campaign_id, variant)

            # 3. Optionally create aspect-ratio-specific source visuals before text rendering.
            if adapt_source_visuals:
                _adapt_source_visuals_for_variant(
                    image_generator=image_generator,
                    source_visual_path=source_visual_path,
                    output_dir=output_dir,
                    variant=variant,
                )
            variant.rendition_paths = []

            # 4. Pick text colors once from the 1:1 reference visual so all ratios stay consistent.
            reference_template = template_for_ratio("1:1")
            reference_source = variant.adapted_source_visual_paths.get("1:1", source_visual_path)
            text_colors = color_selector.select_colors(
                result.campaign,
                product_plan.product,
                reference_source,
                reference_template,
            )

            # 5. Render every aspect-ratio and locale combination deterministically with Pillow.
            for spec in adaptation_specs():
                ratio = str(spec["ratio"])
                render_source = variant.adapted_source_visual_paths.get(ratio, source_visual_path)
                template = template_for_ratio(ratio)
                for localized_text in result.localized_texts.values():
                    variant.rendition_paths.append(
                        renderer.render(
                            result.campaign,
                            render_source,
                            output_dir,
                            template,
                            localized_text=localized_text,
                            text_colors=text_colors,
                        )
                    )

    return result


def _adapt_source_visuals_for_variant(
    image_generator,
    source_visual_path: Path,
    output_dir: Path,
    variant,
) -> None:
    """Generate aspect-ratio-specific source visuals for one asset variant.

    Args:
        image_generator: Image generator implementation with adaptation support.
        source_visual_path: Base source visual to adapt.
        output_dir: Directory where adapted source visuals should be written.
        variant: Asset variant receiving adapted source visual paths and warnings.
    """
    for spec in adaptation_specs():
        ratio = str(spec["ratio"])
        size = spec["size"]
        output_path = output_dir / str(spec["filename"])
        prompt = _adaptation_prompt(spec)
        try:
            image_generator.adapt_source_visual(
                source_visual_path=source_visual_path,
                prompt=prompt,
                output_path=output_path,
                size=size,
            )
        except Exception as exc:
            variant.warnings.append(f"aspect_adaptation {ratio} failed; fell back to crop rendering: {exc}")
            continue
        variant.adapted_source_visual_paths[ratio] = output_path


def _adaptation_prompt(spec: dict[str, object]) -> str:
    """Build an image-edit prompt for aspect-ratio source visual adaptation.

    Args:
        spec: Renderer adaptation spec containing ratio, size, and safe areas.

    Returns:
        Prompt text for the image generation provider.
    """
    return (
        "Recompose and extend this source visual for a final social ad creative. "
        f"Target aspect ratio: {spec['ratio']}. Target output size: {spec['size']}. "
        "Keep the product fully visible and do not crop the product. Preserve product identity, packaging shape, "
        "colors, lighting direction, and the original visual world. Leave clean negative space for deterministic "
        f"text overlay in these normalized safe areas: {spec['safe_areas']}. "
        "Do not render any text, brand logos, CTA buttons, watermarks, or third-party marks in the image."
    )


def format_dry_run(result: DryRunResult, output_root: Path | str) -> str:
    """Format a pipeline result as concise console output.

    Args:
        result: Pipeline result to summarize.
        output_root: Output root displayed in the summary.

    Returns:
        Human-readable multiline status text.
    """
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
            for rendition_path in variant.rendition_paths:
                lines.append(f"    rendition: {rendition_path.as_posix()}")
        for prompt in product_plan.prompts:
            prompt_label = _prompt_label(prompt.prompt_type)
            lines.append(f"    prompt[{prompt.variant_id} {prompt_label}]: {prompt.prompt}")

    return "\n".join(lines)


def _prompt_label(source: AssetSource) -> str:
    """Return a compact label for a prompt source type.

    Args:
        source: Asset source enum value.

    Returns:
        Label used in CLI output.
    """
    if source == AssetSource.GENERATED_FROM_PRODUCT_ASSET:
        return "product-to-source-visual"
    if source == AssetSource.GENERATED_FROM_TEXT:
        return "text-to-source-visual"
    return source.value
