#!/usr/bin/env python3
"""
Tmura - Generate icon.ico
Creates a professional icon with a conversion symbol on blue background.
Outputs icon.ico to both app/resources/ and the project root.
"""

import os
from pathlib import Path


def generate_icon(output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow is required: pip install Pillow")
        return False

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        margin = max(1, size // 16)
        radius = size // 5
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=radius,
            fill=(0, 113, 227, 255)
        )

        bar_h = max(2, size // 10)
        draw.rounded_rectangle(
            [margin, margin, size - margin, margin + bar_h + radius],
            radius=radius,
            fill=(0, 140, 255, 255)
        )

        font_size = int(size * 0.55)
        font = None
        font_candidates = [
            "arial.ttf", "Arial.ttf", "Arial Bold.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for fc in font_candidates:
            try:
                font = ImageFont.truetype(fc, font_size)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default(size=font_size)

        text = "T"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) // 2
        y = (size - th) // 2 - bbox[1]
        draw.text((x + max(1, size // 64), y + max(1, size // 64)), text,
                  fill=(0, 60, 150, 100), font=font)
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

        images.append(img)

    images[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"Icon generated: {output_path}")
    return True


if __name__ == "__main__":
    script_dir = Path(__file__).parent

    resources_dir = script_dir / "app" / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    icon_resources = resources_dir / "icon.ico"

    icon_root = script_dir / "icon.ico"

    if generate_icon(str(icon_resources)):
        import shutil
        shutil.copy2(str(icon_resources), str(icon_root))
        print(f"Icon also placed at: {icon_root}")
        print("Done! Place your own icon.ico in app/resources/ to override this default.")
    else:
        print("Failed to generate icon.")
