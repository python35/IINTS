import argparse
from pathlib import Path

from PIL import Image


def rgb565_bytes(r, g, b):
    value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return bytes((value >> 8, value & 0xFF))


def parse_hex_color(value):
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("Gebruik een kleur zoals #F4F7FA")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def tint_source(source, tint):
    if not tint:
        return source

    tint_rgb = parse_hex_color(tint)
    pixels = source.load()
    for y in range(source.height):
        for x in range(source.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            # Preserve pencil-like texture: dark source strokes become bright tint,
            # light paper areas become subtle.
            luma = (r * 30 + g * 59 + b * 11) // 100
            strength = max(0, 255 - luma)
            pixels[x, y] = (
                tint_rgb[0],
                tint_rgb[1],
                tint_rgb[2],
                min(a, max(25, strength)),
            )
    return source


def make_startup_image(input_path, output_path, preview_path=None, background="#F4F7FA", margin=12, tint=None):
    source = Image.open(input_path).convert("RGBA")
    bbox = source.getbbox()
    if bbox:
        source = source.crop(bbox)
    source = tint_source(source, tint)

    background_rgb = parse_hex_color(background)
    max_size = 240 - margin * 2
    scale = min(max_size / source.width, max_size / source.height)
    new_size = (max(1, int(source.width * scale)), max(1, int(source.height * scale)))
    source = source.resize(new_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (240, 240), background_rgb + (255,))
    x = (240 - source.width) // 2
    y = (240 - source.height) // 2
    canvas.alpha_composite(source, (x, y))
    image = canvas.convert("RGB")

    raw = bytearray()
    pixels = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
    for r, g, b in pixels:
        raw.extend(rgb565_bytes(r, g, b))

    Path(output_path).write_bytes(raw)
    if preview_path:
        image.save(preview_path)


def main():
    parser = argparse.ArgumentParser(description="Maak een 240x240 RGB565 start.raw voor de Pico.")
    parser.add_argument("image", help="Bronafbeelding, bijvoorbeeld PNG of JPG")
    parser.add_argument("-o", "--output", default="start.raw", help="Outputbestand voor de Pico")
    parser.add_argument("--preview", default="start_preview.png", help="PNG-preview van wat op het scherm komt")
    parser.add_argument("--background", default="#F4F7FA", help="Achtergrondkleur voor transparante afbeeldingen")
    parser.add_argument("--margin", type=int, default=12, help="Marge rondom de afbeelding in pixels")
    parser.add_argument("--tint", default=None, help="Tint transparante tekeningen, bijvoorbeeld #EAF6FA")
    args = parser.parse_args()

    make_startup_image(args.image, args.output, args.preview, args.background, args.margin, args.tint)
    print("Gemaakt:", args.output)
    if args.preview:
        print("Preview:", args.preview)


if __name__ == "__main__":
    main()
