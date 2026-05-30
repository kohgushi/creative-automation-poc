from __future__ import annotations

from abc import ABC, abstractmethod

from creative_automation.models import AssetSource, AssetVariant, CampaignBrief, PlannedPrompt, Product
from creative_automation.settings import OpenAISettings, load_openai_settings


class PromptPlannerError(RuntimeError):
    pass


class PromptPlanner(ABC):
    @abstractmethod
    def plan_prompt(self, campaign: CampaignBrief, product: Product, variant: AssetVariant) -> PlannedPrompt | None:
        pass


class RuleBasedPromptPlanner(PromptPlanner):
    def plan_prompt(self, campaign: CampaignBrief, product: Product, variant: AssetVariant) -> PlannedPrompt | None:
        if variant.source == AssetSource.REUSED_SOURCE_VISUAL:
            return None

        prompt_type = variant.source
        prompt = build_rule_based_prompt(campaign, product, variant)
        return PlannedPrompt(
            product_id=product.id,
            variant_id=variant.variant_id,
            prompt_type=prompt_type,
            prompt=prompt,
        )


class OpenAIPromptPlanner(PromptPlanner):
    def __init__(self, settings: OpenAISettings | None = None) -> None:
        self.settings = settings or load_openai_settings()

    def plan_prompt(self, campaign: CampaignBrief, product: Product, variant: AssetVariant) -> PlannedPrompt | None:
        if variant.source == AssetSource.REUSED_SOURCE_VISUAL:
            return None

        if not self.settings.api_key:
            raise PromptPlannerError("OPENAI_API_KEY is required for --prompt-planner openai")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise PromptPlannerError("The openai package is required for --prompt-planner openai") from exc

        client = OpenAI(api_key=self.settings.api_key)
        try:
            response = client.responses.create(
                model=self.settings.text_model,
                input=_openai_instruction(campaign, product, variant),
            )
        except Exception as exc:
            raise PromptPlannerError(f"OpenAI prompt planner request failed: {exc}") from exc
        prompt = response.output_text.strip()
        if not prompt:
            raise PromptPlannerError("OpenAI prompt planner returned an empty prompt")

        return PlannedPrompt(
            product_id=product.id,
            variant_id=variant.variant_id,
            prompt_type=variant.source,
            prompt=prompt,
        )


def get_prompt_planner(name: str) -> PromptPlanner:
    normalized = name.strip().lower()
    if normalized in {"rule-based", "rule_based", "rules"}:
        return RuleBasedPromptPlanner()
    if normalized == "openai":
        return OpenAIPromptPlanner()
    raise PromptPlannerError(f"Unsupported prompt planner: {name}")


def build_rule_based_prompt(campaign: CampaignBrief, product: Product, variant: AssetVariant) -> str:
    visual_direction = _format_visual_direction(campaign)
    visual_notes = f" Product-specific visual notes: {product.visual_notes.rstrip('.')}." if product.visual_notes else ""

    if variant.source == AssetSource.GENERATED_FROM_PRODUCT_ASSET:
        source_clause = (
            "Transform the provided product asset into a campaign-ready source visual. "
            "Preserve the product identity, packaging shape, and recognizable product details."
        )
    elif variant.source == AssetSource.GENERATED_FROM_TEXT:
        source_clause = (
            "Create a campaign-ready source visual from the product description and campaign context. "
            "Make the product concept clear even without an input image."
        )
    else:
        raise PromptPlannerError(f"Cannot build generation prompt for source {variant.source.value}")

    return (
        f"{source_clause} Product: {product.name}. Description: {product.description.rstrip('.')}.{visual_notes} "
        f"Campaign message context: {campaign.campaign_message.rstrip('.')}. Target audience: {campaign.target_audience.rstrip('.')}. "
        f"Market: {campaign.market}. Visual direction: {visual_direction} "
        "Create modern social commerce ad photography with clean negative space for later copy overlay. "
        "Do not render text, logos, labels, watermarks, UI, or CTA in the generated image. "
        "Avoid third-party brands, cluttered backgrounds, unrealistic product shape, and unsupported claims."
    )


def _openai_instruction(campaign: CampaignBrief, product: Product, variant: AssetVariant) -> str:
    base_prompt = build_rule_based_prompt(campaign, product, variant)
    if variant.source == AssetSource.GENERATED_FROM_PRODUCT_ASSET:
        prompt_type = "product-asset-to-source-visual"
    else:
        prompt_type = "text-to-source-visual"

    return (
        "You are a creative production prompt planner. "
        "Write one concise, production-ready prompt for an image generation model. "
        "Return only the prompt text, with no markdown, labels, explanations, or alternatives.\n\n"
        f"Prompt type: {prompt_type}\n"
        f"Draft constraints and context: {base_prompt}"
    )


def _format_visual_direction(campaign: CampaignBrief) -> str:
    if not campaign.visual_direction:
        return "No additional visual direction provided."

    parts: list[str] = []
    for key, value in campaign.visual_direction.items():
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        else:
            rendered = str(value)
        parts.append(f"{key}: {rendered}")
    return "; ".join(parts)
