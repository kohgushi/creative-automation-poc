from pathlib import Path

from creative_automation.asset_store import AssetStore
from creative_automation.brief_loader import load_campaign_brief
from creative_automation.models import AssetSource


def test_asset_store_classifies_sample_assets() -> None:
    brief = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    store = AssetStore(asset_root=Path("input_examples/assets"), output_root=Path("outputs"))

    plans = {plan.product.id: plan for plan in store.build_asset_plan(brief)}

    sparkling_variants = plans["sparkling_lemon_water"].variants
    assert [variant.source for variant in sparkling_variants] == [AssetSource.REUSED_SOURCE_VISUAL]
    assert sparkling_variants[0].variant_id == "source_poolside_can"
    assert sparkling_variants[0].source_visual_path == Path(
        "input_examples/assets/products/sparkling_lemon_water/source_visuals/poolside_can.png"
    )

    berry_variants = plans["berry_energy_bar"].variants
    assert [variant.source for variant in berry_variants] == [AssetSource.GENERATED_FROM_PRODUCT_ASSET]
    assert berry_variants[0].variant_id == "product_wrapper_front"
    assert berry_variants[0].product_asset_path == Path(
        "input_examples/assets/products/berry_energy_bar/product_assets/wrapper_front.png"
    )

    trail_variants = plans["tropical_trail_mix"].variants
    assert [variant.source for variant in trail_variants] == [AssetSource.GENERATED_FROM_TEXT]
    assert trail_variants[0].variant_id == "text_generated"


def test_output_dir_for_variant() -> None:
    brief = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    store = AssetStore(asset_root=Path("input_examples/assets"), output_root=Path("outputs"))
    variant = store.build_asset_plan(brief)[0].variants[0]

    assert store.output_dir_for(brief.campaign_id, variant) == Path(
        "outputs/summer_refresh_2026/sparkling_lemon_water/source_poolside_can"
    )
