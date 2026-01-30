#!/usr/bin/env python3
"""
Generate an animated GIF comparing TCT vs UTF-8 tokenization.
Shows the dramatic difference in token counts side by side.
"""

import argparse
from PIL import Image, ImageDraw, ImageFont


# Colors (dark theme matching GitHub)
COLORS = {
    'bg': '#0d1117',
    'text': '#c9d1d9',
    'text_dim': '#8b949e',
    'tct': '#58a6ff',
    'utf8': '#f0883e',
    'box_bg': '#21262d',
    'json_key': '#7ee787',
    'json_value': '#a5d6ff',
    'json_bracket': '#ffa657',
    'border': '#30363d',
    'success': '#238636',
}


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_font(size: int) -> ImageFont.FreeTypeFont:
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def draw_token_bar(draw, x, y, width, count, max_count, color, label, font, font_small):
    """Draw an animated token bar."""
    bar_height = 35
    bar_width = int((count / max_count) * width) if max_count > 0 else 0

    # Background bar
    draw.rectangle([x, y, x + width, y + bar_height], fill=hex_to_rgb(COLORS['box_bg']))

    # Filled bar
    if bar_width > 0:
        draw.rectangle([x, y, x + bar_width, y + bar_height], fill=hex_to_rgb(color))

    # Label and count
    draw.text((x, y - 22), label, font=font_small, fill=hex_to_rgb(color))
    if count > 0:
        count_text = f"{count} tokens"
        draw.text((x + bar_width + 10, y + 8), count_text, font=font, fill=hex_to_rgb(COLORS['text']))


def create_comparison_frame(
    width: int,
    height: int,
    json_str: str,
    tct_tokens: list,
    utf8_bytes: list,
    tct_visible: int,
    utf8_visible: int,
    font: ImageFont.FreeTypeFont,
    font_small: ImageFont.FreeTypeFont,
    font_title: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Create a single frame comparing TCT vs UTF-8."""

    img = Image.new('RGB', (width, height), hex_to_rgb(COLORS['bg']))
    draw = ImageDraw.Draw(img)

    padding = 30
    y = padding

    # Title
    draw.text((padding, y), "TCT vs UTF-8 Tokenization", font=font_title, fill=hex_to_rgb(COLORS['text']))
    y += 40

    # Separator
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 20

    # Input JSON (truncated if needed)
    draw.text((padding, y), "Input JSON:", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 20

    display_json = json_str if len(json_str) < 80 else json_str[:77] + "..."
    draw.text((padding, y), display_json, font=font, fill=hex_to_rgb(COLORS['text']))
    y += 30

    draw.text((padding, y), f"({len(json_str)} bytes)", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 35

    # Separator
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 25

    # Token comparison bars
    bar_width = width - 2 * padding - 120
    max_count = max(len(utf8_bytes), len(tct_tokens))

    # TCT bar
    draw_token_bar(draw, padding, y, bar_width, tct_visible, max_count,
                   COLORS['tct'], "TCT Tokens", font, font_small)
    y += 60

    # UTF-8 bar
    draw_token_bar(draw, padding, y, bar_width, utf8_visible, max_count,
                   COLORS['utf8'], "UTF-8 Bytes", font, font_small)
    y += 70

    # Compression ratio
    if tct_visible > 0 and utf8_visible > 0:
        ratio = utf8_visible / tct_visible
        ratio_text = f"Compression: {ratio:.1f}x fewer tokens with TCT"
        draw.text((padding, y), ratio_text, font=font, fill=hex_to_rgb(COLORS['success']))

    # Final stats at bottom
    stats_y = height - 40
    draw.line([(padding, stats_y - 15), (width - padding, stats_y - 15)], fill=hex_to_rgb(COLORS['border']), width=1)

    final_text = f"Final: {len(tct_tokens)} TCT tokens vs {len(utf8_bytes)} UTF-8 bytes"
    draw.text((padding, stats_y), final_text, font=font_small, fill=hex_to_rgb(COLORS['text_dim']))

    return img


def generate_comparison_animation(
    json_str: str,
    tct_tokens: list,
    output_path: str,
    width: int = 700,
    height: int = 380,
    frame_duration: int = 100,
):
    """Generate the comparison animated GIF."""

    font = get_font(14)
    font_small = get_font(12)
    font_title = get_font(18)

    utf8_bytes = list(json_str.encode('utf-8'))

    frames = []

    # Animate both filling up simultaneously, but UTF-8 fills faster
    # to show the dramatic difference
    total_steps = 40
    for step in range(total_steps + 1):
        progress = step / total_steps

        # UTF-8 fills linearly
        utf8_visible = int(len(utf8_bytes) * progress)

        # TCT fills at the same rate proportionally
        tct_visible = int(len(tct_tokens) * progress)

        frame = create_comparison_frame(
            width, height,
            json_str,
            tct_tokens,
            utf8_bytes,
            tct_visible,
            utf8_visible,
            font, font_small, font_title
        )
        frames.append(frame)

    # Hold final frame
    for _ in range(20):
        frames.append(frames[-1])

    # Save
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=0
    )

    return len(frames)


def main():
    parser = argparse.ArgumentParser(description="Generate TCT vs UTF-8 comparison GIF")
    parser.add_argument("--json", type=str,
                        default='{"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "nginx"}}',
                        help="JSON string to tokenize")
    parser.add_argument("--output", "-o", type=str, default="../../assets/tct_comparison.gif",
                        help="Output GIF file")
    parser.add_argument("--width", type=int, default=700, help="GIF width")
    parser.add_argument("--height", type=int, default=350, help="GIF height")
    args = parser.parse_args()

    try:
        import tct_kubernetes_bpe_1k as tct
    except ImportError:
        print("Error: Could not import tct_kubernetes_bpe_1k")
        return 1

    tokens = list(tct.encode(args.json))
    utf8_len = len(args.json.encode('utf-8'))

    num_frames = generate_comparison_animation(
        args.json,
        tokens,
        args.output,
        args.width,
        args.height
    )

    print(f"Generated {args.output}")
    print(f"  Input: {args.json}")
    print(f"  TCT: {len(tokens)} tokens")
    print(f"  UTF-8: {utf8_len} bytes")
    print(f"  Compression: {utf8_len / len(tokens):.1f}x")

    return 0


if __name__ == "__main__":
    exit(main())
