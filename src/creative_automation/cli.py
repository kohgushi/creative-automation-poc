from __future__ import annotations

import argparse
from pathlib import Path

from creative_automation.brief_loader import BriefLoadError
from creative_automation.generators import ImageGeneratorError
from creative_automation.pipeline import build_dry_run_result, format_dry_run, run_pipeline
from creative_automation.prompt_planner import PromptPlannerError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Creative automation pipeline")
    parser.add_argument("--brief", type=Path, required=True, help="Path to campaign brief YAML")
    parser.add_argument("--assets", type=Path, required=True, help="Path to input asset root")
    parser.add_argument("--out", type=Path, required=True, help="Path to output root")
    parser.add_argument("--prompt-planner", default="openai", help="Prompt planner provider")
    parser.add_argument("--image-provider", default="openai", help="Image generation provider")
    parser.add_argument("--dry-run", action="store_true", help="Load inputs and print asset classification only")
    parser.add_argument("--show-prompts", action="store_true", help="Generate and print image prompts during dry-run")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.dry_run:
            result = build_dry_run_result(
                args.brief,
                args.assets,
                args.out,
                prompt_planner_name=args.prompt_planner,
                show_prompts=args.show_prompts,
            )
        else:
            result = run_pipeline(
                args.brief,
                args.assets,
                args.out,
                prompt_planner_name=args.prompt_planner,
                image_provider_name=args.image_provider,
            )
    except (BriefLoadError, ImageGeneratorError, PromptPlannerError) as exc:
        parser.error(str(exc))

    print(format_dry_run(result, args.out))
    return 0
