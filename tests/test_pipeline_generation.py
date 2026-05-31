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
    assert sparkling.generated_source_visual_path == (
        tmp_path / "summer_refresh_2026" / "sparkling_lemon_water" / "text_generated" / "generated_source_visual.png"
    )
    assert sparkling.generated_source_visual_path.exists()

    citrus_source, citrus_product = plans["citrus_craft_soda"].variants
    assert citrus_source.prepared_source_visual_path == Path(
        "input_examples/assets/products/citrus_craft_soda/source_visuals/citrus_craft_soda_source_visual.png"
    )
    assert citrus_product.generated_source_visual_path == (
        tmp_path / "summer_refresh_2026" / "citrus_craft_soda" / "product_citrus_craft_soda_product" / "generated_source_visual.png"
    )
    assert citrus_product.generated_source_visual_path.exists()

    tea = plans["peach_black_iced_tea"].variants[0]
    assert tea.generated_source_visual_path == (
        tmp_path / "summer_refresh_2026" / "peach_black_iced_tea" / "product_peach_black_iced_tea_product" / "generated_source_visual.png"
    )
    assert tea.generated_source_visual_path.exists()

    with Image.open(citrus_product.generated_source_visual_path) as image:
        assert image.size == (1024, 1024)

    assert len(plans["sparkling_lemon_water"].prompts) == 1
    assert len(plans["citrus_craft_soda"].prompts) == 1
    assert len(plans["peach_black_iced_tea"].prompts) == 1
