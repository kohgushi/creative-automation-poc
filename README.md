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
          poolside_can.png
        product_assets/
      berry_energy_bar/
        source_visuals/
        product_assets/
          wrapper_front.png
      tropical_trail_mix/
        source_visuals/
        product_assets/
```

## Target Command

```bash
uv run python main.py \
  --brief input_examples/briefs/summer_refresh.yaml \
  --assets input_examples/assets \
  --out outputs \
  --prompt-planner openai \
  --image-provider openai
```

During local development, the existing virtualenv can also be used directly:

```bash
.venv/bin/python main.py \
  --brief input_examples/briefs/summer_refresh.yaml \
  --assets input_examples/assets \
  --out outputs \
  --dry-run

.venv/bin/python -m pytest
.venv/bin/ruff check .
```

## Environment

Create a local `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_TEXT_MODEL=gpt-4.1-mini
OPENAI_IMAGE_MODEL=gpt-image-1
```

Do not commit `.env`.

## Notes

- `SPEC.md` is the source of truth for the product specification.
- `AGENTS.md` contains development guidance for Codex.
- `outputs/` is runtime-generated and ignored by git.
