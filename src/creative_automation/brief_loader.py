from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from creative_automation.models import CampaignBrief


class BriefLoadError(ValueError):
    pass


def load_campaign_brief(path: Path | str) -> CampaignBrief:
    brief_path = Path(path)
    if not brief_path.exists():
        raise BriefLoadError(f"Campaign brief not found: {brief_path}")
    if not brief_path.is_file():
        raise BriefLoadError(f"Campaign brief path is not a file: {brief_path}")

    try:
        raw_data = yaml.safe_load(brief_path.read_text())
    except yaml.YAMLError as exc:
        raise BriefLoadError(f"Failed to parse YAML brief {brief_path}: {exc}") from exc

    if raw_data is None:
        raise BriefLoadError(f"Campaign brief is empty: {brief_path}")
    if not isinstance(raw_data, dict):
        raise BriefLoadError(f"Campaign brief must be a YAML mapping: {brief_path}")

    try:
        return CampaignBrief.model_validate(raw_data)
    except ValidationError as exc:
        raise BriefLoadError(f"Invalid campaign brief {brief_path}: {exc}") from exc
