#!/usr/bin/env python3
"""
Generate extension icons as PNG files.
Run this script to create icons for the extension.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def generate_png_icon(size, output_path):
    """Generate a single PNG icon"""
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
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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

    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    img.save(output_path, 'PNG')
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, "extension", "icons")
    os.makedirs(icons_dir, exist_ok=True)

    sizes = [16, 48, 128]
    for size in sizes:
        output_path = os.path.join(icons_dir, f"icon{size}.png")
        generate_png_icon(size, output_path)

    print("\nAll extension icons generated successfully!")
    print(f"Icons saved to: {icons_dir}")
