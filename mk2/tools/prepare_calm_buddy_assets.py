#!/usr/bin/env python3
"""Prepare small full-character RGB565 assets for IINTS Calm Mode."""

from pathlib import Path
from shutil import copyfile

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets" / "bluey" / "source"
OUTPUT_DIR = ROOT / "assets" / "bluey" / "generated"
DEPLOY_DIR = ROOT / "firmware" / "deploy"
SIZE = 64
MAX_FIGURE_SIZE = 48
PANEL_RGB = (255, 255, 255)

ASSETS = (
    ("happy.jpg", "happy_calm.raw"),
    ("sad.png", "sad_calm.raw"),
    ("angry.png", "angry_calm.raw"),
)


def content_box(image: Image.Image) -> tuple[int, int, int, int]:
    alpha = image.getchannel("A")
    if alpha.getextrema() != (255, 255):
        box = alpha.getbbox()
    else:
        rgb = image.convert("RGB")
        white = Image.new("RGB", image.size, PANEL_RGB)
        difference = ImageChops.difference(rgb, white).convert("L")
        box = difference.point(lambda value: 255 if value > 18 else 0).getbbox()
    return box or (0, 0, image.width, image.height)


def fit_full_character(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    figure = image.crop(content_box(image))
    figure.thumbnail(
        (MAX_FIGURE_SIZE, MAX_FIGURE_SIZE),
        Image.Resampling.LANCZOS,
    )

    panel = Image.new("RGBA", (SIZE, SIZE), PANEL_RGB + (255,))
    x = (SIZE - figure.width) // 2
    y = (SIZE - figure.height) // 2
    panel.alpha_composite(figure, (x, y))
    return panel.convert("RGB")


def write_rgb565(image: Image.Image, output: Path) -> None:
    with output.open("wb") as stream:
        for red, green, blue in image.get_flattened_data():
            value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)
            stream.write(bytes((value >> 8, value & 0xFF)))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    for source_name, output_name in ASSETS:
        image = fit_full_character(ASSET_DIR / source_name)
        output = OUTPUT_DIR / output_name
        write_rgb565(image, output)
        image.save(OUTPUT_DIR / output_name.replace(".raw", "_preview.png"))
        copyfile(output, DEPLOY_DIR / output_name)
        print(output_name)


if __name__ == "__main__":
    main()
