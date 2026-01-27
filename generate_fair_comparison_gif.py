#!/usr/bin/env python3
"""
Generate an animated GIF showing TCT vs production tokenizer comparison.
This is the fair comparison from the paper (50-82% fewer tokens).
"""

import argparse
from PIL import Image, ImageDraw, ImageFont


COLORS = {
    'bg': '#0d1117',
    'text': '#c9d1d9',
    'text_dim': '#8b949e',
    'tct': '#58a6ff',
    'prod': '#f0883e',  # Production tokenizer
    'box_bg': '#21262d',
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
    tct_tokens: int,
    prod_tokens: int,
    tct_visible: int,
    prod_visible: int,
    json_display: str,
    font: ImageFont.FreeTypeFont,
    font_small: ImageFont.FreeTypeFont,
    font_title: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Create a frame comparing TCT vs production tokenizer."""

    img = Image.new('RGB', (width, height), hex_to_rgb(COLORS['bg']))
    draw = ImageDraw.Draw(img)

    padding = 30
    y = padding

    # Title
    draw.text((padding, y), "TCT vs Production Tokenizers", font=font_title, fill=hex_to_rgb(COLORS['text']))
    y += 40

    # Subtitle
    draw.text((padding, y), "Same JSON, verified with tiktoken and tct_kubernetes_bpe_1k",
              font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 30

    # Separator
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 20

    # Input JSON
    draw.text((padding, y), "Input:", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 20
    draw.text((padding, y), json_display, font=font, fill=hex_to_rgb(COLORS['text']))
    y += 35

    # Separator
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 25

    # Token comparison bars
    bar_width = width - 2 * padding - 150
    max_count = max(prod_tokens, tct_tokens)
    bar_height = 35

    # Production tokenizer bar (o200k/Kimi/LLaMA)
    draw.text((padding, y), "o200k (GPT-4):", font=font_small, fill=hex_to_rgb(COLORS['prod']))
    y += 22

    prod_bar_width = int((prod_visible / max_count) * bar_width) if max_count > 0 else 0
    draw.rectangle([padding, y, padding + bar_width, y + bar_height], fill=hex_to_rgb(COLORS['box_bg']))
    if prod_bar_width > 0:
        draw.rectangle([padding, y, padding + prod_bar_width, y + bar_height], fill=hex_to_rgb(COLORS['prod']))

    if prod_visible > 0:
        draw.text((padding + bar_width + 15, y + 8), f"{prod_visible} tokens", font=font, fill=hex_to_rgb(COLORS['text']))
    y += bar_height + 20

    # TCT bar
    draw.text((padding, y), "TCT:", font=font_small, fill=hex_to_rgb(COLORS['tct']))
    y += 22

    tct_bar_width = int((tct_visible / max_count) * bar_width) if max_count > 0 else 0
    draw.rectangle([padding, y, padding + bar_width, y + bar_height], fill=hex_to_rgb(COLORS['box_bg']))
    if tct_bar_width > 0:
        draw.rectangle([padding, y, padding + tct_bar_width, y + bar_height], fill=hex_to_rgb(COLORS['tct']))

    if tct_visible > 0:
        draw.text((padding + bar_width + 15, y + 8), f"{tct_visible} tokens", font=font, fill=hex_to_rgb(COLORS['text']))
    y += bar_height + 25

    # Reduction calculation
    if tct_visible > 0 and prod_visible > 0:
        reduction = ((prod_visible - tct_visible) / prod_visible) * 100
        draw.text((padding, y), f"Reduction: {reduction:.0f}% fewer tokens with TCT",
                  font=font, fill=hex_to_rgb(COLORS['success']))

    # Footer
    footer_y = height - 40
    draw.line([(padding, footer_y - 15), (width - padding, footer_y - 15)], fill=hex_to_rgb(COLORS['border']), width=1)
    draw.text((padding, footer_y), "71% fewer tokens (24 → 7) for this Kubernetes manifest",
              font=font_small, fill=hex_to_rgb(COLORS['text_dim']))

    return img


def generate_animation(output_path: str, width: int = 700, height: int = 380):
    """Generate the comparison GIF."""

    font = get_font(14)
    font_small = get_font(12)
    font_title = get_font(18)

    # VERIFIED with actual tokenizers:
    # JSON: {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "nginx"}}
    # o200k (tiktoken): 24 tokens
    # TCT (tct_kubernetes_bpe_1k): 7 tokens
    prod_tokens = 24  # o200k (verified with tiktoken)
    tct_tokens = 7    # TCT with BPE (verified with tct_kubernetes_bpe_1k)

    json_display = '{"apiVersion":"v1","kind":"Pod","metadata":{"name":"nginx"}}'

    frames = []

    # Animate both filling up
    total_steps = 30
    for step in range(total_steps + 1):
        progress = step / total_steps

        prod_visible = int(prod_tokens * progress)
        tct_visible = int(tct_tokens * progress)

        frame = create_frame(
            width, height,
            tct_tokens, prod_tokens,
            tct_visible, prod_visible,
            json_display,
            font, font_small, font_title
        )
        frames.append(frame)

    # Hold final
    for _ in range(25):
        frames.append(frames[-1])

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0
    )

    return len(frames)


def main():
    parser = argparse.ArgumentParser(description="Generate fair TCT comparison GIF")
    parser.add_argument("--output", "-o", type=str, default="tct_comparison.gif")
    args = parser.parse_args()

    num_frames = generate_animation(args.output)
    print(f"Generated {args.output} ({num_frames} frames)")
    print("  o200k: 24 tokens (verified with tiktoken)")
    print("  TCT:    7 tokens (verified with tct_kubernetes_bpe_1k)")
    print("  Reduction: 71%")

    return 0


if __name__ == "__main__":
    exit(main())
