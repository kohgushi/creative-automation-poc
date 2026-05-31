from pathlib import Path

from PIL import Image

from creative_automation.pipeline import run_pipeline


def test_run_pipeline_renders_final_creatives_with_mock_generator(tmp_path: Path) -> None:
    result = run_pipeline(
        brief_path=Path("input_examples/briefs/summer_refresh.yaml"),
        asset_root=Path("input_examples/assets"),
        output_root=tmp_path,
        prompt_planner_name="rule-based",
        image_provider_name="mock",
    )

    for product_plan in result.products:
        for variant in product_plan.variants:
            assert {path.name for path in variant.rendition_paths} == {"1x1.png", "9x16.png", "16x9.png"}
            for path in variant.rendition_paths:
                assert path.exists()

    sample = (
        tmp_path
        / "summer_refresh_2026"
        / "citrus_craft_soda"
        / "source_citrus_craft_soda_source_visual"
        / "1x1.png"
    )
    with Image.open(sample) as image:
        assert image.size == (1080, 1080)
