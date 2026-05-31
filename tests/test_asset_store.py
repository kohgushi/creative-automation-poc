from pathlib import Path

from creative_automation.asset_store import AssetStore
from creative_automation.brief_loader import load_campaign_brief
from creative_automation.models import AssetSource


def test_asset_store_classifies_sample_assets() -> None:
    brief = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    store = AssetStore(asset_root=Path("input_examples/assets"), output_root=Path("outputs"))

    plans = {plan.product.id: plan for plan in store.build_asset_plan(brief)}

    sparkling_variants = plans["sparkling_lemon_water"].variants
    assert [variant.source for variant in sparkling_variants] == [AssetSource.GENERATED_FROM_TEXT]
    assert sparkling_variants[0].variant_id == "text_generated"

    citrus_variants = plans["citrus_craft_soda"].variants
    assert [variant.source for variant in citrus_variants] == [
        AssetSource.REUSED_SOURCE_VISUAL,
        AssetSource.GENERATED_FROM_PRODUCT_ASSET,
    ]
    assert citrus_variants[0].variant_id == "source_citrus_craft_soda_source_visual"
    assert citrus_variants[0].source_visual_path == Path(
        "input_examples/assets/products/citrus_craft_soda/source_visuals/citrus_craft_soda_source_visual.png"
    )
    assert citrus_variants[1].variant_id == "product_citrus_craft_soda_product"
    assert citrus_variants[1].product_asset_path == Path(
        "input_examples/assets/products/citrus_craft_soda/product_assets/citrus_craft_soda_product.png"
    )

    tea_variants = plans["peach_black_iced_tea"].variants
    assert [variant.source for variant in tea_variants] == [AssetSource.GENERATED_FROM_PRODUCT_ASSET]
    assert tea_variants[0].variant_id == "product_peach_black_iced_tea_product"
    assert tea_variants[0].product_asset_path == Path(
        "input_examples/assets/products/peach_black_iced_tea/product_assets/peach_black_iced_tea_product.png"
    )


def test_output_dir_for_variant() -> None:
    brief = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    store = AssetStore(asset_root=Path("input_examples/assets"), output_root=Path("outputs"))
    variant = store.build_asset_plan(brief)[0].variants[0]

    assert store.output_dir_for(brief.campaign_id, variant) == Path(
        "outputs/summer_refresh_2026/sparkling_lemon_water/text_generated"
    )
