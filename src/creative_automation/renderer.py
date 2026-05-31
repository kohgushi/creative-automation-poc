from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from creative_automation.models import CampaignBrief


@dataclass(frozen=True)
class AspectRatioTemplate:
    ratio: str
    filename: str
    size: tuple[int, int]
    logo_box: tuple[float, float, float, float]
    message_box: tuple[float, float, float, float]
    cta_box: tuple[float, float, float, float]
    logo_size_scale: float
    message_size_scale: float
    cta_size_scale: float

    @property
    def source_visual_filename(self) -> str:
        return f"{self.filename.removesuffix('.png')}_source_visual.png"


TEMPLATES = {
    "1:1": AspectRatioTemplate(
        ratio="1:1",
        filename="1x1.png",
        size=(1080, 1080),
        logo_box=(0.08, 0.05, 0.45, 0.12),
        message_box=(0.08, 0.61, 0.78, 0.81),
        cta_box=(0.08, 0.85, 0.45, 0.95),
        logo_size_scale=0.060,
        message_size_scale=0.075,
        cta_size_scale=0.039,
    ),
    "9:16": AspectRatioTemplate(
        ratio="9:16",
        filename="9x16.png",
        size=(1080, 1920),
        logo_box=(0.08, 0.03, 0.58, 0.09),
        message_box=(0.08, 0.67, 0.86, 0.83),
        cta_box=(0.08, 0.87, 0.50, 0.94),
        logo_size_scale=0.060,
        message_size_scale=0.072,
        cta_size_scale=0.039,
    ),
    "16:9": AspectRatioTemplate(
        ratio="16:9",
        filename="16x9.png",
        size=(1920, 1080),
        logo_box=(0.07, 0.10, 0.42, 0.20),
        message_box=(0.07, 0.30, 0.55, 0.63),
        cta_box=(0.07, 0.68, 0.36, 0.82),
        logo_size_scale=0.057,
        message_size_scale=0.087,
        cta_size_scale=0.041,
    ),
}


class RendererError(RuntimeError):
    pass


class CreativeRenderer:
    def render_all(self, campaign: CampaignBrief, source_visual_path: Path, output_dir: Path) -> list[Path]:
        return [
            self.render(campaign, source_visual_path, output_dir, template)
            for template in TEMPLATES.values()
        ]

    def render(
        self,
        campaign: CampaignBrief,
        source_visual_path: Path,
        output_dir: Path,
        template: AspectRatioTemplate,
    ) -> Path:
        if not source_visual_path.exists():
            raise RendererError(f"Source visual not found: {source_visual_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        canvas = _cover_image(source_visual_path, template.size).convert("RGBA")
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        _draw_readability_gradient(draw, template.size)
        _draw_text_logo(draw, campaign, template)
        _draw_campaign_message(draw, campaign, template)
        _draw_cta(draw, campaign, template)

        final = Image.alpha_composite(canvas, overlay).convert("RGB")
        output_path = output_dir / template.filename
        final.save(output_path)
        return output_path


def adaptation_specs() -> list[dict[str, object]]:
    return [
        {
            "ratio": template.ratio,
            "filename": template.source_visual_filename,
            "size": template.size,
            "safe_areas": {
                "logo": template.logo_box,
                "campaign_message": template.message_box,
                "cta": template.cta_box,
            },
        }
        for template in TEMPLATES.values()
    ]


def template_for_ratio(ratio: str) -> AspectRatioTemplate:
    return TEMPLATES[ratio]


def _cover_image(source_visual_path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(source_visual_path).convert("RGB")
    image_ratio = image.width / image.height
    target_ratio = size[0] / size[1]

    if image_ratio > target_ratio:
        new_height = size[1]
        new_width = round(new_height * image_ratio)
    else:
        new_width = size[0]
        new_height = round(new_width / image_ratio)

    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (new_width - size[0]) // 2
    top = (new_height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def _draw_readability_gradient(draw: ImageDraw.ImageDraw, size: tuple[int, int]) -> None:
    width, height = size
    # Smooth radial-ish overlay centered near the copy area. This avoids hard vertical
    # or horizontal boundaries while keeping text readable over bright source visuals.
    focus_x = width * 0.20
    focus_y = height * 0.76
    max_distance = (width**2 + height**2) ** 0.5
    for y in range(height):
        for x in range(width):
            distance = ((x - focus_x) ** 2 + (y - focus_y) ** 2) ** 0.5
            strength = max(0.0, 1.0 - distance / (max_distance * 0.70))
            alpha = int(125 * strength)
            if alpha:
                draw.point((x, y), fill=(0, 0, 0, alpha))


def _draw_text_logo(draw: ImageDraw.ImageDraw, campaign: CampaignBrief, template: AspectRatioTemplate) -> None:
    box = _box_pixels(template.logo_box, template.size)
    font = _font_for_box(campaign.brand.name, box, template.logo_size_scale, bold=True)
    draw.text((box[0], box[1]), campaign.brand.name.upper(), font=font, fill=_text_color(campaign, "logo"))


def _draw_campaign_message(draw: ImageDraw.ImageDraw, campaign: CampaignBrief, template: AspectRatioTemplate) -> None:
    box = _box_pixels(template.message_box, template.size)
    font = _font_for_box(campaign.campaign_message, box, template.message_size_scale, bold=True)
    lines = _wrap_text(draw, campaign.campaign_message.upper(), font, box[2] - box[0])
    line_height = round(font.size * 1.08)
    total_height = line_height * len(lines)
    y = max(box[1], box[3] - total_height)
    for line in lines:
        draw.text((box[0], y), line, font=font, fill=_text_color(campaign, "campaign_message"))
        y += line_height


def _draw_cta(draw: ImageDraw.ImageDraw, campaign: CampaignBrief, template: AspectRatioTemplate) -> None:
    box = _box_pixels(template.cta_box, template.size)
    font = _font_for_box(campaign.cta, box, template.cta_size_scale, bold=True)
    text = campaign.cta.upper()
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    pad_x = round(font.size * 1.05)
    pad_y = round(font.size * 0.85)
    button_width = min(box[2] - box[0], text_width + pad_x * 2)
    button_height = min(box[3] - box[1], text_height + pad_y * 2)
    button = (box[0], box[1], box[0] + button_width, box[1] + button_height)

    # Liquid-glass style: translucent white fill, soft border, and subtle shadow.
    shadow = (
        button[0] + round(font.size * 0.10),
        button[1] + round(font.size * 0.16),
        button[2] + round(font.size * 0.10),
        button[3] + round(font.size * 0.16),
    )
    draw.rounded_rectangle(shadow, radius=button_height // 2, fill=(0, 0, 0, 52))
    draw.rounded_rectangle(
        button,
        radius=button_height // 2,
        fill=(255, 255, 255, 96),
        outline=(255, 255, 255, 220),
        width=2,
    )
    highlight = (
        button[0] + 3,
        button[1] + 3,
        button[2] - 3,
        button[1] + max(5, button_height // 2),
    )
    draw.rounded_rectangle(highlight, radius=max(4, button_height // 4), fill=(255, 255, 255, 38))
    text_x = button[0] + (button_width - text_width) / 2
    text_y = button[1] + (button_height - text_height) / 2 - font.size * 0.08
    draw.text((text_x + 1, text_y + 1), text, font=font, fill=(0, 0, 0, 90))
    draw.text((text_x, text_y), text, font=font, fill=_text_color(campaign, "cta"))


def _box_pixels(box: tuple[float, float, float, float], size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    return (
        round(box[0] * width),
        round(box[1] * height),
        round(box[2] * width),
        round(box[3] * height),
    )


def _font_for_box(text: str, box: tuple[int, int, int, int], size_scale: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    max_size = max(14, round((box[2] - box[0]) * size_scale))
    min_size = 18
    for size in range(max_size, min_size - 1, -2):
        font = _load_font(size, bold=bold)
        probe = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(probe)
        lines = _wrap_text(draw, text.upper(), font, box[2] - box[0])
        line_height = round(font.size * 1.08)
        if line_height * len(lines) <= box[3] - box[1]:
            return font
    return _load_font(min_size, bold=bold)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _text_color(campaign: CampaignBrief, style_name: str) -> str:
    style = campaign.text_styles.get(style_name, {})
    if isinstance(style, dict) and style.get("color"):
        return str(style["color"])
    return "#ffffff"


def _brand_color(campaign: CampaignBrief, field_name: str, fallback: str) -> str:
    value = getattr(campaign.brand, field_name)
    return value or fallback


def _hex_to_rgba(value: str, alpha: int) -> tuple[int, int, int, int]:
    stripped = value.lstrip("#")
    if len(stripped) != 6:
        return (255, 255, 255, alpha)
    return (
        int(stripped[0:2], 16),
        int(stripped[2:4], 16),
        int(stripped[4:6], 16),
        alpha,
    )
