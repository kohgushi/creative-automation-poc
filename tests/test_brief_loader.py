from pathlib import Path

import pytest

from creative_automation.brief_loader import BriefLoadError, load_campaign_brief


def test_load_sample_brief() -> None:
    brief = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))

    assert brief.campaign_id == "summer_refresh_2026"
    assert brief.brand.name == "Brightside"
    assert len(brief.products) == 3
    assert {product.id for product in brief.products} == {
        "sparkling_lemon_water",
        "citrus_craft_soda",
        "peach_black_iced_tea",
    }


def test_rejects_brief_with_too_few_products(tmp_path: Path) -> None:
    brief_path = tmp_path / "brief.yaml"
    brief_path.write_text(
        """
campaign_id: one_product
market: US
target_audience: Test audience
campaign_message: Test message
cta: Shop now
brand:
  name: Test Brand
products:
  - id: only_product
    name: Only Product
    description: One product is not enough.
""".strip()
    )

    with pytest.raises(BriefLoadError, match="Invalid campaign brief"):
        load_campaign_brief(brief_path)
