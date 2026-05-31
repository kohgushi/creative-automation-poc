from pathlib import Path

from PIL import Image

from creative_automation.generators import MockImageGenerator, OpenAIImageGenerator, get_image_generator


def test_mock_generator_writes_source_visual(tmp_path: Path) -> None:
    output_path = tmp_path / "generated_source_visual.png"

    result = MockImageGenerator().generate_source_visual(
        prompt="Create a source visual with clean negative space.",
        output_path=output_path,
    )

    assert result == output_path
    assert output_path.exists()
    with Image.open(output_path) as image:
        assert image.size == (1024, 1024)


def test_mock_generator_uses_product_asset(tmp_path: Path) -> None:
    product_asset = Path("input_examples/assets/products/peach_black_iced_tea/product_assets/peach_black_iced_tea_product.png")
    output_path = tmp_path / "generated_source_visual.png"

    MockImageGenerator().generate_source_visual(
        prompt="Create a source visual from this product asset.",
        output_path=output_path,
        product_asset_path=product_asset,
    )

    assert output_path.exists()
    with Image.open(output_path) as image:
        assert image.size == (1024, 1024)


def test_mock_generator_adapts_source_visual(tmp_path: Path) -> None:
    source_visual = Path(
        "input_examples/assets/products/citrus_craft_soda/source_visuals/citrus_craft_soda_source_visual.png"
    )
    output_path = tmp_path / "9x16_source_visual.png"

    MockImageGenerator().adapt_source_visual(
        source_visual_path=source_visual,
        prompt="Adapt this source visual for 9:16.",
        output_path=output_path,
        size=(1080, 1920),
    )

    assert output_path.exists()
    with Image.open(output_path) as image:
        assert image.size == (1080, 1920)


def test_get_image_generator_selects_openai_provider() -> None:
    assert isinstance(get_image_generator("openai"), OpenAIImageGenerator)
