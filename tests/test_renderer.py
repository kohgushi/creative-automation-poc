from pathlib import Path

from PIL import Image

from creative_automation.brief_loader import load_campaign_brief
from creative_automation.renderer import CreativeRenderer, TEMPLATES


def test_renderer_outputs_required_dimensions(tmp_path: Path) -> None:
    campaign = load_campaign_brief(Path("input_examples/briefs/summer_refresh.yaml"))
    source_visual = Path("input_examples/assets/products/sparkling_lemon_water/source_visuals/poolside_can.png")

    output_paths = CreativeRenderer().render_all(campaign, source_visual, tmp_path)

    assert {path.name for path in output_paths} == {"1x1.png", "9x16.png", "16x9.png"}
    for path in output_paths:
        with Image.open(path) as image:
            expected_size = next(template.size for template in TEMPLATES.values() if template.filename == path.name)
            assert image.size == expected_size
