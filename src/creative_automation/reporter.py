from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creative_automation.models import DryRunResult


def write_report(result: DryRunResult, report_path: Path | str) -> Path:
    """Write a JSON report for a pipeline run.

    Args:
        result: Pipeline result containing campaign, products, variants, and outputs.
        report_path: Destination path for the JSON report.

    Returns:
        Path to the written report.
    """
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_report_payload(result), indent=2))
    return path


def default_report_path(output_root: Path | str, campaign_id: str) -> Path:
    """Build the conventional report path for a campaign.

    Args:
        output_root: Root output directory.
        campaign_id: Campaign identifier.

    Returns:
        Path to `outputs/<campaign_id>/report.json`.
    """
    return Path(output_root) / campaign_id / "report.json"


def _report_payload(result: DryRunResult) -> dict[str, Any]:
    """Convert a pipeline result into a serializable report payload.

    Args:
        result: Pipeline result to serialize.

    Returns:
        JSON-compatible dictionary with outputs, prompts, warnings, and validation details.
    """
    products = []
    warnings = []
    for product_plan in result.products:
        prompt_by_variant = {prompt.variant_id: prompt.prompt for prompt in product_plan.prompts}
        variants = []
        for variant in product_plan.variants:
            for warning in variant.warnings:
                warnings.append(
                    {
                        "product_id": product_plan.product.id,
                        "variant_id": variant.variant_id,
                        "message": warning,
                    }
                )
            variants.append(
                {
                    "variant_id": variant.variant_id,
                    "asset_source": variant.source.value,
                    "input_path": _path_or_none(variant.input_path),
                    "prepared_source_visual_path": _path_or_none(variant.prepared_source_visual_path),
                    "generated_source_visual_path": _path_or_none(variant.generated_source_visual_path),
                    "adapted_source_visual_paths": {
                        ratio: _path_or_none(path) for ratio, path in variant.adapted_source_visual_paths.items()
                    },
                    "rendition_paths": [_path_or_none(path) for path in variant.rendition_paths],
                    "rendition_paths_by_locale": _rendition_paths_by_locale(variant.rendition_paths),
                    "warnings": variant.warnings,
                    "prompt": prompt_by_variant.get(variant.variant_id),
                }
            )
        products.append(
            {
                "product_id": product_plan.product.id,
                "product_name": product_plan.product.name,
                "variants": variants,
            }
        )

    return {
        "campaign_id": result.campaign.campaign_id,
        "campaign_name": result.campaign.campaign_name,
        "market": result.campaign.market,
        "language": result.campaign.language,
        "target_audience": result.campaign.target_audience,
        "campaign_message": result.campaign.campaign_message,
        "cta": result.campaign.cta,
        "localized_texts": {
            locale: {
                "campaign_message": localized.campaign_message,
                "cta": localized.cta,
            }
            for locale, localized in result.localized_texts.items()
        },
        "brand": {"name": result.campaign.brand.name},
        "products": products,
        "warnings": warnings,
        "validation_results": {
            "brief_loaded": True,
            "product_count": len(result.products),
            "final_creatives_rendered": sum(len(variant.rendition_paths) for product in result.products for variant in product.variants),
        },
    }


def _path_or_none(path: Path | None) -> str | None:
    """Render an optional path as a POSIX string.

    Args:
        path: Optional filesystem path.

    Returns:
        POSIX path string, or `None` when no path exists.
    """
    return path.as_posix() if path else None


def _rendition_paths_by_locale(paths: list[Path]) -> dict[str, list[str]]:
    """Group final rendition paths by locale suffix.

    Args:
        paths: Final creative output paths.

    Returns:
        Mapping from locale code to rendition path strings.
    """
    grouped: dict[str, list[str]] = {}
    for path in paths:
        locale = _locale_from_rendition_name(path.name)
        grouped.setdefault(locale, []).append(path.as_posix())
    return grouped


def _locale_from_rendition_name(filename: str) -> str:
    """Extract a locale code from a rendition filename.

    Args:
        filename: Rendition filename such as `1x1_en.png`.

    Returns:
        Locale suffix, or `default` for non-localized filenames.
    """
    stem = filename.removesuffix(".png")
    parts = stem.split("_")
    return parts[-1] if len(parts) > 1 else "default"
