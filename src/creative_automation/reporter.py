from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creative_automation.models import DryRunResult


def write_report(result: DryRunResult, report_path: Path | str) -> Path:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_report_payload(result), indent=2))
    return path


def default_report_path(output_root: Path | str, campaign_id: str) -> Path:
    return Path(output_root) / campaign_id / "report.json"


def _report_payload(result: DryRunResult) -> dict[str, Any]:
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
    return path.as_posix() if path else None
