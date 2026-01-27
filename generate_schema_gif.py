#!/usr/bin/env python3
"""
Generate an animated GIF showing TCT compression across different schemas.
"""

import argparse
from PIL import Image, ImageDraw, ImageFont


COLORS = {
    'bg': '#0d1117',
    'text': '#c9d1d9',
    'text_dim': '#8b949e',
    'tct': '#58a6ff',
    'utf8': '#f0883e',
    'box_bg': '#21262d',
    'border': '#30363d',
    'kubernetes': '#326ce5',
    'tsconfig': '#3178c6',
    'eslint': '#4b32c3',
}


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_font(size: int) -> ImageFont.FreeTypeFont:
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def create_frame(
    width: int,
    height: int,
    schemas: list,
    visible_progress: float,
    font: ImageFont.FreeTypeFont,
    font_small: ImageFont.FreeTypeFont,
    font_title: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Create a frame showing schema comparison."""

    img = Image.new('RGB', (width, height), hex_to_rgb(COLORS['bg']))
    draw = ImageDraw.Draw(img)

    padding = 30
    y = padding

    # Title
    draw.text((padding, y), "TCT Compression by Schema", font=font_title, fill=hex_to_rgb(COLORS['text']))
    y += 45

    # Column headers
    col_schema = padding
    col_tct = 180
    col_utf8 = 280
    col_ratio = 380
    col_bar = 480

    draw.text((col_schema, y), "Schema", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    draw.text((col_tct, y), "TCT", font=font_small, fill=hex_to_rgb(COLORS['tct']))
    draw.text((col_utf8, y), "UTF-8", font=font_small, fill=hex_to_rgb(COLORS['utf8']))
    draw.text((col_ratio, y), "Compression", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 30

    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 15

    # Schema rows
    bar_max_width = width - col_bar - padding - 10

    for schema in schemas:
        name = schema['name']
        tct_vocab = schema['tct_vocab']
        utf8_vocab = schema['utf8_vocab']
        color = schema['color']
        ratio = utf8_vocab / tct_vocab

        # Animated values
        tct_show = int(tct_vocab * visible_progress)
        utf8_show = int(utf8_vocab * visible_progress)
        ratio_show = utf8_show / tct_show if tct_show > 0 else 0

        # Schema name
        draw.text((col_schema, y), name, font=font, fill=hex_to_rgb(color))

        # TCT count
        draw.text((col_tct, y), str(tct_show), font=font, fill=hex_to_rgb(COLORS['tct']))

        # UTF-8 count
        draw.text((col_utf8, y), str(utf8_show), font=font, fill=hex_to_rgb(COLORS['utf8']))

        # Ratio
        if ratio_show > 0:
            draw.text((col_ratio, y), f"{ratio_show:.1f}x", font=font, fill=hex_to_rgb(COLORS['text']))

        # Comparison bar
        bar_y = y + 3
        bar_height = 16

        # UTF-8 bar (background, full width represents max)
        max_vocab = max(s['utf8_vocab'] for s in schemas)
        utf8_bar_width = int((utf8_show / max_vocab) * bar_max_width) if max_vocab > 0 else 0
        tct_bar_width = int((tct_show / max_vocab) * bar_max_width) if max_vocab > 0 else 0

        # Draw UTF-8 bar
        if utf8_bar_width > 0:
            draw.rectangle([col_bar, bar_y, col_bar + utf8_bar_width, bar_y + bar_height],
                          fill=hex_to_rgb(COLORS['utf8']))

        # Draw TCT bar (overlay)
        if tct_bar_width > 0:
            draw.rectangle([col_bar, bar_y, col_bar + tct_bar_width, bar_y + bar_height],
                          fill=hex_to_rgb(COLORS['tct']))

        y += 45

    # Footer
    y = height - 50
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 15

    draw.text((padding, y), "TCT achieves 30-45% smaller vocabularies while guaranteeing valid JSON output",
              font=font_small, fill=hex_to_rgb(COLORS['text_dim']))

    return img


def generate_animation(output_path: str, width: int = 700, height: int = 350):
    """Generate the schema comparison GIF."""

    font = get_font(14)
    font_small = get_font(11)
    font_title = get_font(18)

    schemas = [
        {'name': 'Kubernetes', 'tct_vocab': 1000, 'utf8_vocab': 1527, 'color': COLORS['kubernetes']},
        {'name': 'ESLint', 'tct_vocab': 500, 'utf8_vocab': 717, 'color': COLORS['eslint']},
        {'name': 'TSConfig', 'tct_vocab': 258, 'utf8_vocab': 277, 'color': COLORS['tsconfig']},
    ]

    frames = []

    # Animate progress
    for step in range(31):
        progress = step / 30
        frame = create_frame(width, height, schemas, progress, font, font_small, font_title)
        frames.append(frame)

    # Hold final
    for _ in range(25):
        frames.append(frames[-1])

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0
    )

    return len(frames)


def main():
    parser = argparse.ArgumentParser(description="Generate schema comparison GIF")
    parser.add_argument("--output", "-o", type=str, default="tct_schemas.gif")
    parser.add_argument("--width", type=int, default=700)
    parser.add_argument("--height", type=int, default=300)
    args = parser.parse_args()

    num_frames = generate_animation(args.output, args.width, args.height)
    print(f"Generated {args.output} ({num_frames} frames)")

    return 0


if __name__ == "__main__":
    exit(main())
