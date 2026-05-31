# Creative Automation POC

This project is a proof-of-concept creative automation pipeline for social campaign assets.

It takes a YAML campaign brief and reusable product assets, prepares source visuals, and renders final social creative variants for multiple aspect ratios.

## Current Scope

The final creative composition is:

```text
source visual + text logo + campaign message + button-like CTA
```

The final POC is expected to use OpenAI for:

- LLM-based image prompt planning.
- Image generation for missing source visuals.
- Aspect-aware source visual adaptation before final rendering.
- LLM-based localization of campaign message and CTA text.

Text placement is handled by a deterministic rendering layer so the logo, campaign message, and CTA remain accurate and reviewable.

## Example Input Layout

```text
input_examples/
  briefs/
    summer_refresh.yaml
  assets/
    products/
      sparkling_lemon_water/
        source_visuals/
        product_assets/
      citrus_craft_soda/
        source_visuals/
          citrus_craft_soda_source_visual.png
        product_assets/
          citrus_craft_soda_product.png
      peach_black_iced_tea/
        source_visuals/
        product_assets/
          peach_black_iced_tea_product.png
```

## Setup

Create or refresh the local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
```

## Environment

Create a local `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_TEXT_MODEL=gpt-4.1-mini
OPENAI_IMAGE_MODEL=gpt-image-1
```

Do not commit `.env`.

## Run

Run the full OpenAI-backed pipeline:

```bash
.venv/bin/python main.py \
  --brief input_examples/briefs/summer_refresh.yaml \
  --assets input_examples/assets \
  --out outputs \
  --prompt-planner openai \
  --image-provider openai \
  --localizer openai \
  --adapt-source-visuals \
  --report
```

During local development, run dry-run validation before using external APIs:

```bash
.venv/bin/python main.py \
  --brief input_examples/briefs/summer_refresh.yaml \
  --assets input_examples/assets \
  --out outputs \
  --dry-run

.venv/bin/python -m pytest
.venv/bin/ruff check .
```

## Output

Runtime outputs are written to `outputs/<campaign_id>/`:

```text
outputs/summer_refresh_2026/
  report.json
  sparkling_lemon_water/
    text_generated/
      generated_source_visual.png
      1x1_source_visual.png
      9x16_source_visual.png
      16x9_source_visual.png
      1x1_en.png
      1x1_ja.png
      9x16_en.png
      9x16_ja.png
      16x9_en.png
      16x9_ja.png
  citrus_craft_soda/
    source_citrus_craft_soda_source_visual/
      1x1_source_visual.png
      9x16_source_visual.png
      16x9_source_visual.png
      1x1_en.png
      1x1_ja.png
      9x16_en.png
      9x16_ja.png
      16x9_en.png
      16x9_ja.png
    product_citrus_craft_soda_product/
      generated_source_visual.png
      1x1_source_visual.png
      9x16_source_visual.png
      16x9_source_visual.png
      1x1_en.png
      1x1_ja.png
      9x16_en.png
      9x16_ja.png
      16x9_en.png
      16x9_ja.png
  peach_black_iced_tea/
    product_peach_black_iced_tea_product/
      generated_source_visual.png
      1x1_source_visual.png
      9x16_source_visual.png
      16x9_source_visual.png
      1x1_en.png
      1x1_ja.png
      9x16_en.png
      9x16_ja.png
      16x9_en.png
      16x9_ja.png
```

## Design Decisions

- Existing source visuals are reused instead of regenerated.
- Product assets are converted into source visuals through image generation.
- Products without assets are generated from the product description and campaign context.
- Source visuals can be adapted per aspect ratio so products are less likely to be cut off by final crops.
- Final creative filenames include locale codes so language variants are easy to review side by side.
- OpenAI is the concrete LLM and image generation provider for this POC.
- Text logo, campaign message, and CTA are rendered deterministically with Pillow instead of relying on image generation models to render text.
- The renderer uses fixed aspect-ratio templates for reliable `1:1`, `9:16`, and `16:9` outputs.

## Assumptions and Limitations

- Input briefs are YAML.
- Input assets are PNG files.
- Product `description` includes the main benefit or selling point.
- The company logo is rendered as styled text, not an image file.
- Generated outputs are review-ready local files, not automatically published ads.
- The current layout templates are intentionally simple and can be replaced by brand-approved templates later.
- `outputs/` is runtime-generated and ignored by git.

## Notes

- `SPEC.md` is the source of truth for the product specification.
- `AGENTS.md` contains development guidance for Codex.
