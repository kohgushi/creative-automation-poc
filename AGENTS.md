# AGENTS.md

## Project Goal

Build a proof-of-concept creative automation pipeline for social ad campaigns.

The pipeline turns a campaign brief and reusable product assets into final social creative variants by combining:

- A source visual.
- A company logo rendered as styled text.
- A campaign message.
- A button-like CTA.

Follow `SPEC.md` as the source of truth for product behavior, data contracts, and terminology.

## Current Product Direction

Use these terms consistently:

- `source visual`: the main image used as the base for final creative composition.
- `product asset`: a product-only image such as a cutout, packshot, or isolated product render.
- `asset variant`: one source visual candidate for one product.
- `final creative`: the rendered social ad image.
- `rendition`: one final creative exported for a specific aspect ratio.

The final POC must use:

- OpenAI-backed LLM prompt planning.
- OpenAI-backed image generation.
- Deterministic rendering for text logo, campaign message, and CTA.

Mock generators and rule-based prompt planners may be added for local development and deterministic tests, but they are not sufficient for final submission.

## Required Pipeline Behavior

The solution must:

- Accept a campaign brief in YAML.
- Include at least two products.
- Require each product to have `id`, `name`, and `description`.
- Treat product `description` as including the main product benefit or selling point.
- Accept local input assets from `input_examples/assets`.
- Reuse existing source visuals when available.
- Generate source visuals from product assets when source visuals are missing.
- Generate source visuals from product text when both source visuals and product assets are missing.
- Produce final creatives for `1:1`, `9:16`, and `16:9`.
- Render the company logo as styled text, not as an image asset.
- Render the campaign message and a button-like CTA on every final creative.
- Save outputs by campaign, product, asset variant, and aspect ratio.

## Data Layout Rules

Canonical sample input paths:

```text
input_examples/
  briefs/
    summer_refresh.yaml
  assets/
    products/
      <product_id>/
        source_visuals/
          *.png
        product_assets/
          *.png
```

Runtime outputs go under:

```text
outputs/<campaign_id>/<product_id>/<asset_variant_id>/
```

`outputs/` is runtime-generated and should stay gitignored.

Do not reintroduce older input directories such as `examples/` or root-level `input_assets/`.

## Module Boundaries

Use a Python CLI with core pipeline logic under `src/creative_automation/`.

Core modules:

- `cli.py`: CLI argument parsing and execution entrypoint.
- `pipeline.py`: orchestration across loading, asset discovery, prompt planning, generation, rendering, and reporting.
- `models.py`: Pydantic data models and validation.
- `brief_loader.py`: YAML loading and validation.
- `asset_store.py`: asset discovery and output path management.
- `prompt_planner.py`: prompt planner interface, OpenAI LLM planner, and optional rule-based development planner.
- `generators.py`: image generation provider interface, OpenAI image generator, and optional mock generator.
- `renderer.py`: Pillow-based final creative rendering.
- `settings.py`: environment variables and default configuration.

Optional modules:

- `reporter.py`: JSON report generation.
- `compliance.py`: brand and legal checks.

Dependency direction:

- `cli.py` calls `pipeline.py`.
- `pipeline.py` orchestrates the other modules.
- Lower-level modules depend on `models.py`.
- Lower-level modules must not import `cli.py`.
- Provider-specific OpenAI code should stay inside `prompt_planner.py`, `generators.py`, or a small helper if needed.

Keep `main.py` thin. It should delegate to the package CLI rather than contain business logic.

## Milestone Workflow

Follow `MILESTONES.md` for implementation order.

Do not skip milestones unless the user explicitly asks. At the end of each milestone, report:

- Changed files.
- Verification commands.
- Completion criteria status.
- Known limitations.
- Next recommended milestone.

## Clarification Rule

When implementation raises a meaningful product, architecture, data contract, API-cost, output-quality, or milestone-scope question, stop and ask the user before choosing unilaterally.

Make the question specific and include the tradeoff. Do not ask for routine low-risk implementation details that are already covered by `SPEC.md`, `MILESTONES.md`, or local code patterns.

## CLI Shape

Target final command:

```bash
uv run python main.py \
  --brief input_examples/briefs/summer_refresh.yaml \
  --assets input_examples/assets \
  --out outputs \
  --prompt-planner openai \
  --image-provider openai
```

Development and test paths may support `--prompt-planner rule-based` and `--image-provider mock`, but OpenAI-backed execution is required for final submission.

## Environment Variables

Use `.env` for local secrets and model configuration:

```text
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=gpt-4.1-mini
OPENAI_IMAGE_MODEL=gpt-image-1
```

Never commit `.env` or real API keys. Keep `.env.example` safe to commit.

## Implementation Principles

- Keep the POC explainable and demo-friendly.
- Keep business logic in `src/creative_automation/`.
- Keep file and module names explicit.
- Use structured parsing and validation for campaign briefs.
- Keep provider-specific OpenAI code behind small interfaces.
- Do not rely on image generation models for final text rendering.
- Use Pillow for deterministic text overlay and aspect-ratio rendering.
- Preserve existing user changes unless explicitly asked to remove them.

## Development Commands

Use `uv` for dependency management.

For Codex-driven routine verification in this environment, prefer the existing virtualenv commands because `uv run` may rewrite `uv.lock` or hit cache/network constraints:

```bash
.venv/bin/python main.py --brief input_examples/briefs/summer_refresh.yaml --assets input_examples/assets --out outputs --dry-run
.venv/bin/python -m pytest
.venv/bin/ruff check .
```

For user-side local execution, `uv` commands are still acceptable:

```bash
uv sync
uv run python main.py --brief input_examples/briefs/summer_refresh.yaml --assets input_examples/assets --out outputs --prompt-planner openai --image-provider openai
uv run pytest
uv run ruff check .
```

## Testing Expectations

Add focused tests where they provide useful confidence:

- Campaign brief parsing and validation.
- Asset discovery and asset variant expansion.
- Prompt planning behavior.
- Output path organization.
- Renderer output behavior.
- Optional report generation if implemented.
