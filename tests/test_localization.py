from pathlib import Path

import pytest

from creative_automation.brief_loader import load_campaign_brief
from creative_automation.localization import LocalizationError, RuleBasedLocalizer, get_localizer


def test_rule_based_localizer_keeps_english_source_text() -> None:
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))

    localized = RuleBasedLocalizer().localize(campaign)

    assert localized["en"].campaign_message == campaign.campaign_message
    assert localized["en"].cta == campaign.cta
    assert localized["ja"].campaign_message.startswith("[ja] ")
    assert localized["ja"].cta.startswith("[ja] ")


def test_get_localizer_rejects_unknown_provider() -> None:
    with pytest.raises(LocalizationError, match="Unsupported localizer"):
        get_localizer("unknown")
