# MILESTONES.md

## Development Rule

Work through milestones in order unless explicitly redirected.

Each milestone should end with:

- Changed files.
- Verification commands.
- Completion criteria status.
- Known limitations.
- Next milestone handoff.

Keep `SPEC.md` as the product specification and `AGENTS.md` as the development guidance. This file controls implementation sequence.

## Milestone 1: Data Model and Asset Discovery

Goal:

Load the campaign brief and classify asset variants without calling external APIs.

Modules:

- `src/creative_automation/models.py`
- `src/creative_automation/brief_loader.py`
- `src/creative_automation/asset_store.py`
- Minimal `src/creative_automation/pipeline.py`
- Minimal `src/creative_automation/cli.py`
- `main.py`
- Focused tests

Scope:

- Parse `input_examples/briefs/summer_refresh.yaml`.
- Validate required campaign and product fields.
- Discover product folders under `input_examples/assets/products`.
- Classify asset variants as:
  - `reused_source_visual`
  - `generated_from_product_asset`
  - `generated_from_text`
- Add a dry-run mode that prints classification results.

Completion Criteria:

- The sample YAML loads successfully.
- At least two products are validated.
- `sparkling_lemon_water` has a reusable source visual variant.
- `berry_energy_bar` has a product-asset-generated variant.
- `tropical_trail_mix` has a text-generated variant.
- Dry-run output shows product ids, asset variant ids, and asset source classification.
- Tests pass for brief loading and asset discovery.

Out of Scope:

- OpenAI calls.
- Prompt generation.
- Source visual generation.
- Final creative rendering.

## Milestone 2: Prompt Planning

Goal:

Generate image prompts for source visual creation.

Modules:

- `src/creative_automation/prompt_planner.py`
- `src/creative_automation/settings.py`
- Tests for prompt planning

Scope:

- Define a prompt planner interface.
- Implement a rule-based prompt planner for deterministic tests.
- Implement an OpenAI-backed prompt planner for final execution.
- Support prompt types:
  - product asset to source visual
  - text to source visual
- Include campaign context, product description, visual direction, negative space guidance, and "no rendered text" guidance.

Completion Criteria:

- Rule-based planner produces stable prompts without API calls.
- OpenAI planner can be selected by CLI.
- Dry-run can print generated prompts without image generation.
- Tests cover prompt content for both prompt types.

Out of Scope:

- Image generation.
- Final creative rendering.

## Milestone 3: Source Visual Generation

Goal:

Prepare source visuals for all asset variants.

Modules:

- `src/creative_automation/generators.py`
- `src/creative_automation/settings.py`
- Pipeline integration
- Tests for mock generation and output paths

Scope:

- Define an image generator interface.
- Implement a mock generator for local development and tests.
- Implement an OpenAI-backed image generator for final execution.
- Reuse existing source visuals without regeneration.
- Generate source visuals from product assets.
- Generate source visuals from text-only product context.
- Save generated source visuals under the appropriate output variant folder.

Completion Criteria:

- Existing source visual variants are reused.
- Product asset variants produce `generated_source_visual.png`.
- Text-only variants produce `generated_source_visual.png`.
- Mock generator path works in tests.
- OpenAI generator can be selected by CLI.

Out of Scope:

- Final creative rendering.
- JSON reporting.

## Milestone 4: Creative Rendering

Goal:

Render final creative renditions for all prepared source visuals.

Modules:

- `src/creative_automation/renderer.py`
- Pipeline integration
- Renderer tests

Scope:

- Implement `1:1`, `9:16`, and `16:9` templates.
- Resize/crop source visuals for each aspect ratio.
- Render brand name as styled text.
- Render campaign message as text.
- Render CTA as a button-like element.
- Preserve safe margins and readability.

Completion Criteria:

- Each asset variant produces:
  - `1x1.png`
  - `9x16.png`
  - `16x9.png`
- Final creatives contain text logo, campaign message, and CTA.
- Renderer tests validate output dimensions.

Out of Scope:

- Advanced visual design optimization.
- Localization.

## Milestone 5: End-to-End OpenAI Run

Goal:

Run the full pipeline with OpenAI prompt planning and OpenAI image generation.

Modules:

- Pipeline integration
- CLI integration
- Settings validation

Scope:

- Load `.env` or environment variables.
- Validate OpenAI configuration.
- Run with `--prompt-planner openai --image-provider openai`.
- Keep provider boundaries generic while requiring only OpenAI as the concrete real provider.

Completion Criteria:

- The target command completes successfully with real OpenAI calls.
- Outputs are organized by campaign, product, asset variant, and aspect ratio.
- Existing source visuals are not regenerated.
- Generated source visuals are saved for missing source visual cases.

Out of Scope:

- Additional provider implementations.

## Milestone 6: Report, Documentation, and Demo Polish

Goal:

Make the project submission-ready and easy to present.

Modules:

- `src/creative_automation/reporter.py`
- Optional `src/creative_automation/compliance.py`
- README updates

Scope:

- Generate optional `report.json`.
- Include output paths, asset source status, prompts, warnings, and validation results.
- Update README with setup, run commands, input examples, output examples, key design decisions, assumptions, and limitations.
- Add curated example outputs if useful.

Completion Criteria:

- README is sufficient to run the project locally.
- Report is generated when requested.
- The project can be demoed from a fresh checkout with `.env` configured.

Out of Scope:

- Production approval workflows.
- Social publishing.
- Analytics.

## Milestone 7: Aspect-Aware Source Visual Adaptation

Goal:

Prevent products from being cut off when source visuals are rendered into `1:1`, `9:16`, and `16:9` final creatives.

Modules:

- `src/creative_automation/renderer.py`
- `src/creative_automation/generators.py`
- `src/creative_automation/pipeline.py`
- `src/creative_automation/reporter.py`
- CLI integration
- Focused tests

Scope:

- Expose renderer template safe areas for image adaptation prompts.
- Add an image generator interface for aspect-aware source visual adaptation.
- Implement a mock adaptation path for tests.
- Implement an OpenAI-backed adaptation path for final execution.
- Add `--adapt-source-visuals`.
- Generate one adapted source visual per asset variant and aspect ratio:
  - `1x1_source_visual.png`
  - `9x16_source_visual.png`
  - `16x9_source_visual.png`
- Render final creatives from adapted source visuals when available.
- Fall back to existing crop rendering if adaptation fails for a ratio.
- Record adaptation warnings and adapted source visual paths in `report.json`.

Completion Criteria:

- Existing source visual variants and generated source visual variants can both be adapted.
- Mock pipeline produces adapted source visual files for all three aspect ratios.
- Final creatives still render for all variants and aspect ratios.
- Report includes adapted source visual paths and adaptation warnings.
- Tests pass.

Out of Scope:

- Localization.
- Legal review.
- Object detection or segmentation-based smart crop.
