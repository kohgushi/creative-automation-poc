# Creative Automation POC Specification

## 1. Objective

Define a local creative automation pipeline that turns a campaign brief and reusable assets into social creative variants.

The pipeline generates final creatives by combining:

- A source visual.
- A company logo rendered as styled text.
- A campaign message.
- A CTA.

The system should support multiple products, multiple source/product assets per product, and multiple social aspect ratios.

## 2. Scope

### 2.1 Minimum Scope

The minimum implementation must:

- Accept a campaign brief in YAML.
- Validate that the brief contains at least two products.
- Validate that each product has an `id`, `name`, and `description`.
- Validate that the brief contains target market, target audience, campaign message, CTA, and brand name.
- Accept local input assets.
- Reuse existing source visuals when available.
- Generate source visuals when required.
- Use a real LLM for image prompt planning.
- Use a real image generation API for source visual generation.
- Include an OpenAI-backed implementation for both prompt planning and image generation.
- Render final creatives for `1:1`, `9:16`, and `16:9`.
- Render the company logo as styled text.
- Render the campaign message and CTA on each final creative.
- Render the CTA as button-like text.
- Save outputs organized by campaign, product, asset variant, and aspect ratio.
- Run locally through a command-line interface.

### 2.2 Optional Scope

The following features are optional and should not block the minimum local pipeline:

- Brand compliance checks such as required element presence and brand color usage.
- Simple legal checks for prohibited words or risky claims.
- Localized campaign text beyond English.
- More advanced prompt templates and visual quality controls.
- Additional image generation providers beyond OpenAI.
- Mock-only execution for local development and deterministic tests.

The following optional feature is implemented for demo traceability:

- JSON report containing output paths, asset source, prompt text, warnings, and validation results.
- Aspect-aware source visual adaptation for each final aspect ratio.
- LLM-backed localization for campaign message and CTA.

### 2.3 Non-Goals

The POC will not:

- Publish assets directly to social platforms.
- Implement approval workflows for brand, legal, or marketing teams.
- Implement a dashboard or analytics product.
- Require cloud storage for the default workflow.
- Require external API credentials for dry-run validation or mock-based local development.
- Rely on image generation models to render final text.

## 3. Creative Model

### 3.1 Terminology

- `Campaign`: one marketing campaign with a shared message, target audience, market, brand, and CTA.
- `Product`: one product included in the campaign.
- `Source visual`: the main visual image used as the base for final creative composition. It may be an existing approved image or a generated image.
- `Product asset`: a product-only image such as a cutout, packshot, or isolated product render.
- `Asset variant`: one source visual candidate for one product. Existing source visuals and generated source visuals both become asset variants.
- `Final creative`: the rendered social ad image containing the source visual, text logo, campaign message, and CTA.
- `Rendition`: one final creative exported for a specific aspect ratio.
- `Prompt planner`: an LLM-backed component that turns campaign, product, visual direction, and asset context into image-generation prompts.
- `Aspect-aware source visual`: a source visual adapted for one final aspect ratio before text overlay.
- `Localized creative text`: the campaign message and CTA translated or adapted for one output locale.

### 3.2 Expansion Model

The pipeline expands one campaign brief into final creatives using this structure:

```text
campaign
  x products
  x asset variants
  x aspect ratios
  x locales
  = final creative renditions
```

For example:

```text
1 campaign x 2 products x 2 asset variants x 3 aspect ratios x 2 locales = 24 final creatives
```

### 3.3 Final Creative Composition

Each final creative contains:

- Source visual as the base image.
- Brand name rendered as a text logo.
- Campaign message rendered as text.
- CTA rendered as button-like text.

Product name and product description are not displayed by default. They are used for asset discovery, prompt planning, source visual generation, and reporting.

## 4. Input Contract

### 4.1 Campaign Brief

The canonical campaign brief format is YAML.

Recommended path:

```text
input_examples/briefs/summer_refresh.yaml
```

Required root fields:

- `campaign_id`: stable identifier used for output folder naming.
- `market`: target region or market.
- `target_audience`: target audience description.
- `campaign_message`: message displayed on every final creative.
- `cta`: CTA displayed on every final creative.
- `brand`: brand configuration.
- `products`: list of at least two products.

Optional root fields:

- `campaign_name`: human-readable campaign name.
- `language`: campaign language. Defaults to `en` if omitted.
- `locales`: output locale list. Defaults to `["en"]` if omitted.
- `visual_direction`: campaign-level visual guidance for source visual generation.
- `text_styles`: rendering configuration for text logo, campaign message, and CTA.

### 4.2 Brand Fields

Required brand fields:

- `name`: company or brand name rendered as a text logo.

Optional brand fields:

- `primary_color`: default campaign accent color.
- `secondary_color`: secondary campaign color.

Brand color usage:

- `primary_color` is campaign metadata for the main brand accent and may be used by future templates or style defaults.
- `secondary_color` is campaign metadata for a supporting brand accent and may be used by future templates or style defaults.
- Explicit values in `text_styles` control rendered text colors when provided.

Example:

```yaml
brand:
  name: Brightside
  primary_color: "#FFD84D"
  secondary_color: "#C73659"
```

### 4.3 Product Fields

Required product fields:

- `id`: stable product identifier used for asset discovery and output paths.
- `name`: human-readable product name.
- `description`: short product description. It should include the product's main benefit or selling point because there is no separate `key_benefit` field.

Optional product fields:

- `visual_notes`: product-specific visual guidance for prompt planning.

Example:

```yaml
products:
  - id: sparkling_lemon_water
    name: Sparkling Lemon Water
    description: A zero-sugar sparkling water with natural lemon flavor and a bright citrus refreshment benefit.
    visual_notes: Show condensation, citrus slices, and a refreshing summer feel.
```

### 4.4 Visual Direction

`visual_direction` provides campaign-level guidance for source visual generation. It is used by the prompt planner and image generator, not displayed directly on final creatives.

Example:

```yaml
visual_direction:
  setting: sunny outdoor summer scene
  style: modern social commerce ad photography
  mood:
    - fresh
    - bright
    - optimistic
  composition: product-forward with clean negative space for copy
  negative_space: lower-left
  avoid:
    - rendered text
    - third-party logos
    - cluttered background
    - unrealistic product shape
```

### 4.5 Text Styles

Text styles are optional. If omitted, the renderer uses sensible defaults.

The logo is rendered as text, not as an image.

Example:

```yaml
text_styles:
  logo:
    font_family: DejaVu Sans
    font_weight: bold
    italic: false
    color: "#FFFFFF"
    size_scale: 0.045

  campaign_message:
    font_family: DejaVu Sans
    font_weight: bold
    italic: false
    color: "#FFFFFF"
    size_scale: 0.085

  cta:
    font_family: DejaVu Sans
    font_weight: bold
    italic: false
    color: "#FFFFFF"
    size_scale: 0.035
    button:
      enabled: true
      border_color: "#FFFFFF"
      fill_color: null
```

### 4.6 Example Brief

```yaml
campaign_id: summer_refresh_2026
campaign_name: Summer Refresh Launch
market: US
language: en
locales:
  - en
  - ja
target_audience: Health-conscious millennials
campaign_message: Refresh your summer with bright, feel-good flavor.
cta: Shop now

brand:
  name: Brightside
  primary_color: "#FFD84D"
  secondary_color: "#C73659"

visual_direction:
  setting: sunny outdoor summer scene
  style: modern social commerce ad photography
  mood:
    - fresh
    - bright
  composition: product-forward with clean negative space for copy
  negative_space: lower-left
  avoid:
    - rendered text
    - cluttered background

products:
  - id: sparkling_lemon_water
    name: Sparkling Lemon Water
    description: A zero-sugar sparkling water with natural lemon flavor and a bright citrus refreshment benefit.
    visual_notes: Show condensation, citrus slices, and a refreshing summer feel.

  - id: berry_energy_bar
    name: Berry Energy Bar
    description: A plant-based berry and oat energy bar for convenient fuel during busy summer days.
```

### 4.7 Asset Library

Recommended asset root:

```text
input_examples/assets/
```

Brand assets are currently not required because the company logo is rendered as text.

Product assets are organized by product id:

```text
input_examples/assets/products/<product_id>/
  source_visuals/
    <source_visual_name>.png
  product_assets/
    <product_asset_name>.png
```

Example:

```text
input_examples/assets/
  products/
    sparkling_lemon_water/
      source_visuals/
        poolside_can.png
        beach_table.png
      product_assets/
        can_front.png

    berry_energy_bar/
      product_assets/
        wrapper_front.png
        wrapper_stack.png
```

### 4.8 Asset Discovery Rules

For each product, the pipeline discovers asset variants in this order:

1. Existing source visuals:
   - Every file under `source_visuals/*.png` becomes one reusable asset variant.
2. Product assets:
   - Every file under `product_assets/*.png` is used to generate one source visual asset variant.
3. No assets:
   - If neither source visuals nor product assets exist, generate one source visual from the product description and campaign context.

The pipeline may process multiple asset variants per product. This supports scalable batch generation while still allowing the demo dataset to remain small.

## 5. Output Contract

### 5.1 Runtime Output Layout

Runtime outputs are written under:

```text
outputs/<campaign_id>/
```

Each product and asset variant gets a dedicated folder:

```text
outputs/<campaign_id>/
  <product_id>/
    <asset_variant_id>/
      source_visual.png
      generated_source_visual.png
      1x1_source_visual.png
      9x16_source_visual.png
      16x9_source_visual.png
      1x1.png
      9x16.png
      16x9.png
      1x1_en.png
      1x1_ja.png
      9x16_en.png
      9x16_ja.png
      16x9_en.png
      16x9_ja.png
```

Notes:

- `source_visual.png` is optional and may be a copied reusable source visual.
- `generated_source_visual.png` is created only when the pipeline generates a source visual.
- `<ratio>_source_visual.png` is created when aspect-aware source visual adaptation is enabled.
- Final creative filenames use stable ratio names: `1x1.png`, `9x16.png`, and `16x9.png`.
- When localization is enabled, final creative filenames include the locale: `1x1_en.png`, `1x1_ja.png`, `9x16_en.png`, etc.
- `outputs/` is runtime-generated and should generally be ignored by git.

### 5.2 Aspect Ratios

Required final creative sizes:

| Ratio | Filename | Size |
| --- | --- | --- |
| `1:1` | `1x1.png` | `1080x1080` |
| `9:16` | `9x16.png` | `1080x1920` |
| `16:9` | `16x9.png` | `1920x1080` |

### 5.3 Report

When `--report` is provided, the report is written to:

```text
outputs/<campaign_id>/report.json
```

The report includes:

- Campaign id.
- Product ids.
- Asset variant ids.
- Asset source: `reused_source_visual`, `generated_from_product_asset`, or `generated_from_text`.
- Generated prompt text, if available.
- Localized campaign message and CTA text.
- Final creative output paths.
- Warnings and validation results.

## 6. Pipeline Flow

1. Parse CLI arguments.
2. Load and validate the campaign brief.
3. Discover asset variants for each product.
4. For each product and asset variant:
   - Reuse existing source visual if available.
   - Otherwise generate a source visual from a product asset.
   - Otherwise generate a source visual from product text and campaign context.
5. If enabled, adapt each source visual for each configured aspect ratio using image generation.
6. Localize campaign message and CTA for each configured locale.
7. Render final creatives for each configured aspect ratio and locale.
8. Save final creatives to the product and asset variant output folder.
9. Optionally run validation checks.
10. Write `report.json` when `--report` is provided.
11. Print concise execution results to the console.

## 7. Rendering and Generation Strategy

### 7.1 Source Visual Selection

Existing source visuals are preferred because they represent approved or campaign-ready visual assets.

When source visuals do not exist, the pipeline prepares generated source visuals from product assets or product text.

### 7.2 Prompt Planning

The prompt planner creates image-generation prompts. It does not render final text into images.

The final POC must include a real OpenAI-backed LLM prompt planner. A rule-based prompt planner may still exist for local development and deterministic tests, but it is not sufficient for the final submission.

The prompt planner supports two prompt types:

1. Product-to-source-visual prompt:
   - Used when product assets exist but source visuals do not.
   - Should preserve product identity.
   - Should place the product into the campaign visual context.
   - Should request clean negative space for later text overlay.
2. Text-to-source-visual prompt:
   - Used when neither source visuals nor product assets exist.
   - Should create a campaign-ready source visual from product description, campaign context, and visual direction.
   - Should avoid rendered text, third-party logos, and unsupported claims.

The prompt planner interface should remain provider-agnostic, but only the OpenAI implementation is required for this POC.

### 7.3 Image Generation

Image generation is used to create source visuals, not final text-bearing creatives.

Provider behavior:

- `openai`: required real provider for final source visual generation.
- `mock`: optional development and test provider for fast local iteration and deterministic tests.

The generator interface should remain provider-agnostic, but only the OpenAI implementation is required for this POC. The generator should receive a prompt and optional product asset path, then write a source visual image to disk.

### 7.4 Template-Based Text Overlay

Final text is rendered by a deterministic rendering layer.

The renderer places:

- Text logo.
- Campaign message.
- CTA as a button-like element.

This avoids relying on image generation models for text accuracy, spelling, brand consistency, or legal reviewability.

### 7.5 Aspect-Aware Source Visual Adaptation

When `--adapt-source-visuals` is enabled, every prepared source visual is adapted once per final aspect ratio before text rendering.

The adaptation step uses the source visual as an input image and asks the image generation provider to recompose or extend it for the target aspect ratio. The prompt includes:

- Target aspect ratio and output size.
- Logo, campaign message, and CTA safe areas.
- A requirement to keep the product fully visible.
- A requirement to preserve product identity, package shape, and visual context.
- A requirement to leave copy areas clean.
- A requirement to avoid rendered text, third-party logos, or unsupported claims.

Adapted source visuals are saved as:

```text
outputs/<campaign_id>/<product_id>/<asset_variant_id>/
  1x1_source_visual.png
  9x16_source_visual.png
  16x9_source_visual.png
```

If adaptation fails for a ratio, the pipeline records a warning and falls back to rendering from the prepared source visual using the existing crop behavior. This keeps demos and batch runs from failing completely because of a single image adaptation issue.

### 7.6 Aspect-Ratio Layout Rules

Phase 1 uses fixed templates per aspect ratio:

- `1:1`: source visual full-bleed, logo near top-left, campaign message in lower-left or lower third, CTA below message.
- `9:16`: source visual full-bleed, logo near top, campaign message in lower third, CTA near bottom.
- `16:9`: source visual full-bleed, logo and message on the left, CTA below message.

The renderer should preserve safe margins and keep text readable with overlays, shadows, or contrast panels when needed.

### 7.7 LLM Localization

The source campaign language is assumed to be English.

When multiple output locales are configured, the pipeline uses an LLM localizer to create localized campaign message and CTA text. The `en` locale uses the original English `campaign_message` and `cta` without an LLM call.

Localized text is used only by the deterministic renderer. Image generation prompts and source visual adaptation remain based on the source brief.

Final creative filenames include locale codes so demos can show language variants together:

```text
outputs/<campaign_id>/<product_id>/<asset_variant_id>/
  1x1_en.png
  1x1_ja.png
  9x16_en.png
  9x16_ja.png
  16x9_en.png
  16x9_ja.png
```

## 8. CLI Contract

Target command:

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

Arguments:

- `--brief`: path to YAML campaign brief.
- `--assets`: path to local asset root.
- `--out`: path to output root.
- `--prompt-planner`: prompt planner provider name. Final POC supports `openai`; local development may support `rule-based`.
- `--image-provider`: image generation provider name. Final POC supports `openai`; local development may support `mock`.
- `--localizer`: localization provider name. Final POC supports `openai`; local development may support `rule-based`.
- `--adapt-source-visuals`: generate aspect-ratio-specific source visuals before final text rendering.

Future optional arguments may include:

- `--max-assets-per-product`: limit asset expansion for compact demos.

Implemented optional arguments:

- `--report`: write `outputs/<campaign_id>/report.json`.

## 9. Module Boundaries

Minimum viable modules:

- `src/creative_automation/cli.py`: command-line orchestration.
- `src/creative_automation/models.py`: Pydantic data models and validation.
- `src/creative_automation/brief_loader.py`: YAML loading.
- `src/creative_automation/asset_store.py`: asset discovery and output path management.
- `src/creative_automation/prompt_planner.py`: prompt planner interface, OpenAI LLM planner, and optional rule-based development planner.
- `src/creative_automation/localization.py`: localization interface, OpenAI LLM localizer, and optional rule-based development localizer.
- `src/creative_automation/generators.py`: image generation provider interface, OpenAI image generator, and optional mock generator.
- `src/creative_automation/renderer.py`: Pillow final creative rendering.

Optional modules:

- `src/creative_automation/compliance.py`: brand and legal checks.

Implemented supporting modules:

- `src/creative_automation/reporter.py`: JSON report generation.

`main.py` should stay thin and call the package CLI.

## 10. Assumptions and Limitations

Assumptions:

- Campaign briefs are YAML in Phase 1.
- Input assets are PNG files in Phase 1.
- Product descriptions include the product's main benefit or selling point.
- Product name and description are not displayed on final creatives by default.
- The logo is rendered as styled text, not loaded from an image file.
- Final creatives are review-ready files, not automatically published ads.
- Final submission runs with OpenAI-backed prompt planning and image generation.

Limitations:

- Mock image generation will not match the quality of a real generative image model.
- Provider boundaries are generic, but only OpenAI is required as a concrete real provider.
- Phase 1 does not perform real legal review.
- Phase 1 does not support cloud storage.
- Phase 1 does not include campaign publishing, analytics, or approval workflows.
