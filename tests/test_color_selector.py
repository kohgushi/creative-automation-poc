from pathlib import Path

from creative_automation.brief_loader import load_campaign_brief
from creative_automation.color_selector import RuleBasedColorSelector, select_brand_color
from creative_automation.renderer import template_for_ratio


def test_rule_based_color_selector_returns_valid_colors() -> None:
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    product = next(product for product in campaign.products if product.id == "citrus_craft_soda")
    source_visual = Path(
        "input_examples/assets/products/citrus_craft_soda/source_visuals/citrus_craft_soda_source_visual.png"
    )

    colors = RuleBasedColorSelector().select_colors(campaign, product, source_visual, template_for_ratio("1:1"))

    assert colors.campaign_message.startswith("#")
    assert colors.cta == colors.campaign_message
    assert colors.brand in {campaign.brand.primary_color, campaign.brand.secondary_color}


def test_select_brand_color_prefers_higher_contrast_candidate() -> None:
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))

    color = select_brand_color(campaign, background_brightness=240, fallback="#00687D")

    assert color == campaign.brand.secondary_color
