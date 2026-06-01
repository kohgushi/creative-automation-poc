from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from creative_automation.settings import OpenAISettings, SettingsError, load_openai_settings, validate_openai_settings


class ImageGeneratorError(RuntimeError):
    """Raised when source visual generation or adaptation fails."""

    pass


class ImageGenerator(ABC):
    """Interface for source visual generation providers."""

    @abstractmethod
    def generate_source_visual(
        self,
        prompt: str,
        output_path: Path,
        product_asset_path: Path | None = None,
    ) -> Path:
        """Generate a campaign-ready source visual.

        Args:
            prompt: Image generation prompt.
            output_path: Destination image path.
            product_asset_path: Optional product-only image to use as input.

        Returns:
            Path to the generated source visual.
        """
        pass

    @abstractmethod
    def adapt_source_visual(
        self,
        source_visual_path: Path,
        prompt: str,
        output_path: Path,
        size: tuple[int, int],
    ) -> Path:
        """Adapt a source visual to a target aspect-ratio canvas.

        Args:
            source_visual_path: Input source visual path.
            prompt: Image-edit prompt.
            output_path: Destination image path.
            size: Target pixel dimensions.

        Returns:
            Path to the adapted source visual.
        """
        pass


class MockImageGenerator(ImageGenerator):
    """Deterministic Pillow generator used for tests and local development."""

    def generate_source_visual(
        self,
        prompt: str,
        output_path: Path,
        product_asset_path: Path | None = None,
    ) -> Path:
        """Create a mock source visual without external API calls.

        Args:
            prompt: Prompt text embedded into the mock image for traceability.
            output_path: Destination image path.
            product_asset_path: Optional product asset composited into the mock image.

        Returns:
            Path to the generated mock source visual.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (1024, 1024), "#f7d86a")
        draw = ImageDraw.Draw(image)

        for y in range(1024):
            shade = int(245 - (y / 1024) * 50)
            draw.line((0, y, 1024, y), fill=(shade, min(240, shade + 20), 210))

        if product_asset_path:
            product = Image.open(product_asset_path).convert("RGBA")
            product.thumbnail((520, 520))
            x = 1024 - product.width - 100
            y = 260
            shadow = Image.new("RGBA", product.size, (0, 0, 0, 55))
            image.paste(shadow, (x + 18, y + 24), shadow)
            image.paste(product, (x, y), product)
        else:
            draw.rounded_rectangle((570, 280, 840, 760), radius=44, fill="#ffffff", outline="#2b2b2b", width=6)
            draw.ellipse((620, 340, 790, 510), fill="#f6b73c")
            draw.rectangle((650, 560, 760, 700), fill="#2b7a78")

        draw.rounded_rectangle((80, 700, 560, 900), radius=36, fill=(255, 255, 255), outline="#ffffff")
        font = ImageFont.load_default()
        draw.text((110, 735), "MOCK SOURCE VISUAL", fill="#1f2933", font=font)
        draw.text((110, 770), _shorten(prompt), fill="#1f2933", font=font)

        image.save(output_path)
        return output_path

    def adapt_source_visual(
        self,
        source_visual_path: Path,
        prompt: str,
        output_path: Path,
        size: tuple[int, int],
    ) -> Path:
        """Create a mock aspect-adapted source visual.

        Args:
            source_visual_path: Input source visual path.
            prompt: Prompt text embedded into the mock image for traceability.
            output_path: Destination image path.
            size: Target pixel dimensions.

        Returns:
            Path to the adapted mock image.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        source = Image.open(source_visual_path).convert("RGB")
        background = _cover(source, size).filter(ImageFilter.GaussianBlur(radius=24))
        foreground = source.copy()
        foreground.thumbnail((round(size[0] * 0.82), round(size[1] * 0.82)))

        canvas = background.convert("RGBA")
        x = (size[0] - foreground.width) // 2
        y = (size[1] - foreground.height) // 2
        canvas.alpha_composite(foreground.convert("RGBA"), (x, y))

        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        draw.text((24, 24), f"MOCK ADAPTED {size[0]}x{size[1]}", fill="#ffffff", font=font)
        draw.text((24, 44), _shorten(prompt, 80), fill="#ffffff", font=font)
        canvas.convert("RGB").save(output_path)
        return output_path


class OpenAIImageGenerator(ImageGenerator):
    """OpenAI-backed source visual generator and adapter."""

    def __init__(self, settings: OpenAISettings | None = None) -> None:
        """Initialize the generator.

        Args:
            settings: Optional OpenAI settings. Defaults to environment-backed settings.
        """
        self.settings = settings or load_openai_settings()

    def generate_source_visual(
        self,
        prompt: str,
        output_path: Path,
        product_asset_path: Path | None = None,
    ) -> Path:
        """Generate a source visual using OpenAI image APIs.

        Args:
            prompt: Image generation or edit prompt.
            output_path: Destination image path.
            product_asset_path: Optional product image for image-edit generation.

        Returns:
            Path to the generated source visual.

        Raises:
            ImageGeneratorError: If settings, import, API call, or image data fail.
        """
        try:
            validate_openai_settings(self.settings, require_image_model=True)
        except SettingsError as exc:
            raise ImageGeneratorError(str(exc)) from exc

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImageGeneratorError("The openai package is required for --image-provider openai") from exc

        client = OpenAI(api_key=self.settings.api_key)

        try:
            if product_asset_path:
                with product_asset_path.open("rb") as image_file:
                    response = client.images.edit(
                        model=self.settings.image_model,
                        image=image_file,
                        prompt=prompt,
                        size="1024x1024",
                    )
            else:
                response = client.images.generate(
                    model=self.settings.image_model,
                    prompt=prompt,
                    size="1024x1024",
                )
        except Exception as exc:
            raise ImageGeneratorError(f"OpenAI image generation request failed: {exc}") from exc

        b64_json = response.data[0].b64_json if response.data else None
        if not b64_json:
            raise ImageGeneratorError("OpenAI image generator returned no image data")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(base64.b64decode(b64_json))
        return output_path

    def adapt_source_visual(
        self,
        source_visual_path: Path,
        prompt: str,
        output_path: Path,
        size: tuple[int, int],
    ) -> Path:
        """Adapt a source visual to a target aspect ratio using OpenAI image edit.

        Args:
            source_visual_path: Input source visual path.
            prompt: Aspect adaptation prompt.
            output_path: Destination image path.
            size: Target pixel dimensions.

        Returns:
            Path to the adapted source visual.

        Raises:
            ImageGeneratorError: If settings, import, API call, or image data fail.
        """
        try:
            validate_openai_settings(self.settings, require_image_model=True)
        except SettingsError as exc:
            raise ImageGeneratorError(str(exc)) from exc

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImageGeneratorError("The openai package is required for --image-provider openai") from exc

        client = OpenAI(api_key=self.settings.api_key)
        try:
            with source_visual_path.open("rb") as image_file:
                response = client.images.edit(
                    model=self.settings.image_model,
                    image=image_file,
                    prompt=prompt,
                    size=_openai_size(size),
                )
        except Exception as exc:
            raise ImageGeneratorError(f"OpenAI source visual adaptation request failed: {exc}") from exc

        b64_json = response.data[0].b64_json if response.data else None
        if not b64_json:
            raise ImageGeneratorError("OpenAI source visual adaptation returned no image data")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(base64.b64decode(b64_json))
        return output_path


def get_image_generator(name: str) -> ImageGenerator:
    """Create an image generator by provider name.

    Args:
        name: Provider name such as `mock` or `openai`.

    Returns:
        Image generator implementation.

    Raises:
        ImageGeneratorError: If the provider name is unsupported.
    """
    normalized = name.strip().lower()
    if normalized == "mock":
        return MockImageGenerator()
    if normalized == "openai":
        return OpenAIImageGenerator()
    raise ImageGeneratorError(f"Unsupported image provider: {name}")


def _shorten(text: str, limit: int = 95) -> str:
    """Shorten prompt text for embedding in mock images.

    Args:
        text: Source text to shorten.
        limit: Maximum output length.

    Returns:
        Original text or an ellipsized version.
    """
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize and crop an image to cover a target canvas.

    Args:
        image: Source image.
        size: Target pixel dimensions.

    Returns:
        Cropped RGB image exactly matching the requested size.
    """
    image = image.convert("RGB")
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


def _openai_size(size: tuple[int, int]) -> str:
    """Map renderer dimensions to supported OpenAI image sizes.

    Args:
        size: Renderer target dimensions.

    Returns:
        OpenAI image size string.
    """
    if size == (1080, 1920):
        return "1024x1536"
    if size == (1920, 1080):
        return "1536x1024"
    return "1024x1024"
