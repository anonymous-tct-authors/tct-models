#!/usr/bin/env python3
"""
Generate an animated GIF showing TCT's zero-entropy elimination.
Shows how TCT skips predicting deterministic syntax, focusing only on semantic decisions.
"""

import argparse
from PIL import Image, ImageDraw, ImageFont


COLORS = {
    'bg': '#0d1117',
    'text': '#c9d1d9',
    'text_dim': '#8b949e',
    'syntax': '#f85149',      # Red - deterministic, skipped
    'semantic': '#58a6ff',    # Blue - model predicts these
    'box_bg': '#21262d',
    'border': '#30363d',
    'success': '#238636',
    'highlight': '#ffa657',
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
    step: int,
    total_steps: int,
    font: ImageFont.FreeTypeFont,
    font_small: ImageFont.FreeTypeFont,
    font_title: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Create a frame showing zero-entropy elimination."""

    img = Image.new('RGB', (width, height), hex_to_rgb(COLORS['bg']))
    draw = ImageDraw.Draw(img)

    padding = 25
    y = padding

    # Title
    draw.text((padding, y), "Zero-Entropy Elimination", font=font_title, fill=hex_to_rgb(COLORS['text']))
    y += 40

    # Explanation
    draw.text((padding, y), "TCT skips predicting deterministic syntax - models only predict at decision points",
              font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 35

    # The JSON structure with annotations
    # {"kind": "Pod", "name": "nginx"}

    # Define tokens: (text, type, description)
    # type: 'syntax' = deterministic, 'semantic' = model predicts
    tokens = [
        ('{', 'syntax', 'auto'),
        ('"kind"', 'syntax', 'auto'),
        (':', 'syntax', 'auto'),
        ('"', 'syntax', 'auto'),
        ('Pod', 'semantic', 'predict'),
        ('"', 'syntax', 'auto'),
        (',', 'syntax', 'auto'),
        ('"name"', 'syntax', 'auto'),
        (':', 'syntax', 'auto'),
        ('"', 'syntax', 'auto'),
        ('nginx', 'semantic', 'predict'),
        ('"', 'syntax', 'auto'),
        ('}', 'syntax', 'auto'),
    ]

    # Calculate which tokens to show
    visible_tokens = min(step, len(tokens))

    # Draw section header
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 15

    # Legend
    legend_y = y
    draw.rectangle([padding, legend_y, padding + 12, legend_y + 12], fill=hex_to_rgb(COLORS['syntax']))
    draw.text((padding + 18, legend_y - 2), "Syntax (auto-emitted)", font=font_small, fill=hex_to_rgb(COLORS['syntax']))

    draw.rectangle([padding + 200, legend_y, padding + 212, legend_y + 12], fill=hex_to_rgb(COLORS['semantic']))
    draw.text((padding + 218, legend_y - 2), "Semantic (model predicts)", font=font_small, fill=hex_to_rgb(COLORS['semantic']))
    y += 30

    # Draw JSON with colored tokens
    json_y = y + 10
    cursor_x = padding

    for i, (text, token_type, desc) in enumerate(tokens):
        if i >= visible_tokens:
            # Draw placeholder
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text((cursor_x, json_y), "░" * len(text), font=font, fill=hex_to_rgb(COLORS['border']))
            cursor_x += text_width + 2
            continue

        color = COLORS['syntax'] if token_type == 'syntax' else COLORS['semantic']

        # Highlight current token
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if i == visible_tokens - 1:
            # Current token - add background highlight
            draw.rectangle([cursor_x - 2, json_y - 2, cursor_x + text_width + 2, json_y + 18],
                          fill=hex_to_rgb(COLORS['box_bg']),
                          outline=hex_to_rgb(color), width=2)

        draw.text((cursor_x, json_y), text, font=font, fill=hex_to_rgb(color))
        cursor_x += text_width + 2

    y = json_y + 50

    # Stats section
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 15

    # Count syntax vs semantic tokens shown
    syntax_count = sum(1 for i, (_, t, _) in enumerate(tokens) if i < visible_tokens and t == 'syntax')
    semantic_count = sum(1 for i, (_, t, _) in enumerate(tokens) if i < visible_tokens and t == 'semantic')

    total_syntax = sum(1 for _, t, _ in tokens if t == 'syntax')
    total_semantic = sum(1 for _, t, _ in tokens if t == 'semantic')

    # Draw counters
    draw.text((padding, y), "Syntax tokens (skipped):", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    draw.text((padding + 180, y), f"{syntax_count}/{total_syntax}", font=font, fill=hex_to_rgb(COLORS['syntax']))

    draw.text((padding + 280, y), "Semantic tokens (predicted):", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    draw.text((padding + 480, y), f"{semantic_count}/{total_semantic}", font=font, fill=hex_to_rgb(COLORS['semantic']))
    y += 35

    # Progress bar showing predictions saved
    if visible_tokens > 0:
        bar_width = width - 2 * padding
        bar_y = y

        # Total bar
        draw.rectangle([padding, bar_y, padding + bar_width, bar_y + 20],
                      fill=hex_to_rgb(COLORS['box_bg']))

        # Show proportion
        total_shown = syntax_count + semantic_count
        if total_shown > 0:
            syntax_width = int((syntax_count / total_shown) * bar_width)
            semantic_width = int((semantic_count / total_shown) * bar_width)

            draw.rectangle([padding, bar_y, padding + syntax_width, bar_y + 20],
                          fill=hex_to_rgb(COLORS['syntax']))
            draw.rectangle([padding + syntax_width, bar_y, padding + syntax_width + semantic_width, bar_y + 20],
                          fill=hex_to_rgb(COLORS['semantic']))

        y += 30

        # Summary text
        if total_shown > 0:
            pct_saved = (syntax_count / total_shown) * 100
            draw.text((padding, y),
                     f"TCT eliminates {pct_saved:.0f}% of predictions (zero-entropy syntax)",
                     font=font, fill=hex_to_rgb(COLORS['success']))

    # Footer
    footer_y = height - 35
    draw.line([(padding, footer_y - 10), (width - padding, footer_y - 10)], fill=hex_to_rgb(COLORS['border']), width=1)
    draw.text((padding, footer_y), "Models focus capacity on semantic decisions, not mandatory syntax",
              font=font_small, fill=hex_to_rgb(COLORS['text_dim']))

    return img


def generate_animation(output_path: str, width: int = 750, height: int = 380):
    """Generate the zero-entropy elimination GIF."""

    font = get_font(16)
    font_small = get_font(12)
    font_title = get_font(20)

    frames = []
    total_tokens = 13  # Number of tokens in our example

    # Initial frame
    for _ in range(5):
        frame = create_frame(width, height, 0, total_tokens, font, font_small, font_title)
        frames.append(frame)

    # Animate tokens appearing
    for step in range(1, total_tokens + 1):
        for _ in range(3):  # Hold each step for 3 frames
            frame = create_frame(width, height, step, total_tokens, font, font_small, font_title)
            frames.append(frame)

    # Hold final
    for _ in range(20):
        frames.append(frames[-1])

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=120,
        loop=0
    )

    return len(frames)


def main():
    parser = argparse.ArgumentParser(description="Generate zero-entropy elimination GIF")
    parser.add_argument("--output", "-o", type=str, default="../../assets/tct_zero_entropy.gif")
    parser.add_argument("--width", type=int, default=750)
    parser.add_argument("--height", type=int, default=380)
    args = parser.parse_args()

    num_frames = generate_animation(args.output, args.width, args.height)
    print(f"Generated {args.output} ({num_frames} frames)")

    return 0


if __name__ == "__main__":
    exit(main())
