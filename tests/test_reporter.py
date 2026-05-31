import json
from pathlib import Path

from creative_automation.pipeline import run_pipeline
from creative_automation.reporter import default_report_path, write_report


def test_write_report_for_pipeline_result(tmp_path: Path) -> None:
    result = run_pipeline(
        brief_path=Path("input_examples/briefs/summer_refresh.yaml"),
        asset_root=Path("input_examples/assets"),
        output_root=tmp_path,
        prompt_planner_name="rule-based",
        image_provider_name="mock",
    )
    report_path = write_report(result, default_report_path(tmp_path, result.campaign.campaign_id))

    payload = json.loads(report_path.read_text())

    assert payload["campaign_id"] == "summer_refresh_2026"
    assert payload["validation_results"]["product_count"] == 3
    assert payload["validation_results"]["final_creatives_rendered"] == 12
    assert payload["products"][0]["variants"][0]["rendition_paths"]


def test_write_report_includes_adapted_source_visual_paths(tmp_path: Path) -> None:
    result = run_pipeline(
        brief_path=Path("input_examples/briefs/summer_refresh.yaml"),
        asset_root=Path("input_examples/assets"),
        output_root=tmp_path,
        prompt_planner_name="rule-based",
        image_provider_name="mock",
        adapt_source_visuals=True,
    )
    report_path = write_report(result, default_report_path(tmp_path, result.campaign.campaign_id))

    payload = json.loads(report_path.read_text())
    first_variant = payload["products"][0]["variants"][0]

    assert set(first_variant["adapted_source_visual_paths"]) == {"1:1", "9:16", "16:9"}
    assert first_variant["warnings"] == []


def test_default_report_path() -> None:
    assert default_report_path("outputs", "campaign") == Path("outputs/campaign/report.json")
