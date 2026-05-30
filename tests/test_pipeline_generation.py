from pathlib import Path

from PIL import Image

from creative_automation.pipeline import prepare_source_visuals


def test_prepare_source_visuals_with_mock_generator(tmp_path: Path) -> None:
    result = prepare_source_visuals(
        brief_path=Path("input_examples/briefs/summer_refresh.yaml"),
        asset_root=Path("input_examples/assets"),
        output_root=tmp_path,
        prompt_planner_name="rule-based",
        image_provider_name="mock",
    )

    plans = {plan.product.id: plan for plan in result.products}

    sparkling = plans["sparkling_lemon_water"].variants[0]
    assert sparkling.prepared_source_visual_path == Path(
        "input_examples/assets/products/sparkling_lemon_water/source_visuals/poolside_can.png"
    )

    berry = plans["berry_energy_bar"].variants[0]
    assert berry.generated_source_visual_path == (
        tmp_path / "summer_refresh_2026" / "berry_energy_bar" / "product_wrapper_front" / "generated_source_visual.png"
    )
    assert berry.generated_source_visual_path.exists()

    trail = plans["tropical_trail_mix"].variants[0]
    assert trail.generated_source_visual_path == (
        tmp_path / "summer_refresh_2026" / "tropical_trail_mix" / "text_generated" / "generated_source_visual.png"
    )
    assert trail.generated_source_visual_path.exists()

    with Image.open(berry.generated_source_visual_path) as image:
        assert image.size == (1024, 1024)

    assert len(plans["berry_energy_bar"].prompts) == 1
    assert len(plans["tropical_trail_mix"].prompts) == 1
