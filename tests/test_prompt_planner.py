from pathlib import Path

import pytest

from creative_automation.asset_store import AssetStore
from creative_automation.brief_loader import load_campaign_brief
from creative_automation.models import AssetSource
from creative_automation.prompt_planner import PromptPlannerError, RuleBasedPromptPlanner, get_prompt_planner


def test_rule_based_prompt_for_product_asset_variant() -> None:
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    product_plan = _plan_for_product("berry_energy_bar")
    variant = product_plan.variants[0]
    planner = RuleBasedPromptPlanner()

    planned = planner.plan_prompt(campaign, product_plan.product, variant)

    assert planned is not None
    assert planned.prompt_type == AssetSource.GENERATED_FROM_PRODUCT_ASSET
    assert "Transform the provided product asset" in planned.prompt
    assert "Berry Energy Bar" in planned.prompt
    assert "clean negative space" in planned.prompt
    assert "Do not render text" in planned.prompt
    assert "third-party brands" in planned.prompt


def test_rule_based_prompt_for_text_variant() -> None:
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    product_plan = _plan_for_product("tropical_trail_mix")
    variant = product_plan.variants[0]
    planner = RuleBasedPromptPlanner()

    planned = planner.plan_prompt(campaign, product_plan.product, variant)

    assert planned is not None
    assert planned.prompt_type == AssetSource.GENERATED_FROM_TEXT
    assert "Create a campaign-ready source visual from the product description" in planned.prompt
    assert "Tropical Trail Mix" in planned.prompt
    assert "sunny outdoor summer scene" in planned.prompt
    assert "Do not render text" in planned.prompt


def test_rule_based_prompt_skips_reused_source_visual() -> None:
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    product_plan = _plan_for_product("sparkling_lemon_water")
    variant = product_plan.variants[0]
    planner = RuleBasedPromptPlanner()

    assert planner.plan_prompt(campaign, product_plan.product, variant) is None


def test_get_prompt_planner_rejects_unknown_provider() -> None:
    with pytest.raises(PromptPlannerError, match="Unsupported prompt planner"):
        get_prompt_planner("unknown")


def _plan_for_product(product_id: str):
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    store = AssetStore(asset_root=Path("input_examples/assets"), output_root=Path("outputs"))
    plans = {plan.product.id: plan for plan in store.build_asset_plan(campaign)}
    return plans[product_id]
