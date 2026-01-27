#!/usr/bin/env python3
"""
Generate an animated GIF showing TCT tokenization for README embedding.

This creates a visual animation showing:
1. Input JSON
2. Tokens appearing one by one
3. Progressive decoding of the JSON output
4. Compression statistics
"""

import argparse
import json
from PIL import Image, ImageDraw, ImageFont
from typing import Optional


# Colors (dark theme matching GitHub)
COLORS = {
    'bg': '#0d1117',
    'text': '#c9d1d9',
    'text_dim': '#8b949e',
    'token': '#58a6ff',
    'token_bg': '#21262d',
    'json_key': '#7ee787',
    'json_value': '#a5d6ff',
    'json_bracket': '#ffa657',
    'highlight': '#f85149',
    'progress': '#238636',
    'border': '#30363d',
}


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a monospace font, falling back to default if needed."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue

    # Fallback to default
    return ImageFont.load_default()


def create_frame(
    width: int,
    height: int,
    title: str,
    input_json: str,
    tokens: list,
    visible_tokens: int,
    decoded_json: str,
    step_info: str,
    font: ImageFont.FreeTypeFont,
    font_small: ImageFont.FreeTypeFont,
    font_title: ImageFont.FreeTypeFont,
    utf8_byte_count: int = 0,
) -> Image.Image:
    """Create a single frame of the animation."""

    img = Image.new('RGB', (width, height), hex_to_rgb(COLORS['bg']))
    draw = ImageDraw.Draw(img)

    padding = 25
    y = padding

    # Title with subtle underline
    draw.text((padding, y), title, font=font_title, fill=hex_to_rgb(COLORS['text']))
    y += 35
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 15

    # Input section
    draw.text((padding, y), "Input JSON:", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 22

    # Draw input JSON with syntax highlighting
    json_height = draw_json_colored(draw, padding, y, input_json, font, width - 2 * padding)
    y += max(json_height, 20)

    # Tokens section header with count
    token_label = f"TCT Tokens ({visible_tokens}/{len(tokens)}):"
    draw.text((padding, y), token_label, font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 25

    # Draw token boxes
    token_x = padding
    token_box_width = 48
    token_box_height = 28
    token_spacing = 56

    # Calculate how many tokens fit per row
    tokens_per_row = (width - 2 * padding) // token_spacing

    for i, token in enumerate(tokens):
        row = i // tokens_per_row
        col = i % tokens_per_row
        x = token_x + col * token_spacing
        current_y = y + row * (token_box_height + 8)

        if i < visible_tokens:
            # Draw filled box with rounded corners effect
            draw.rectangle(
                [x, current_y, x + token_box_width, current_y + token_box_height],
                fill=hex_to_rgb(COLORS['token_bg']),
                outline=hex_to_rgb(COLORS['token']),
                width=2
            )
            # Draw token number
            token_str = str(token)
            bbox = draw.textbbox((0, 0), token_str, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (x + (token_box_width - text_width) // 2, current_y + 4),
                token_str,
                font=font,
                fill=hex_to_rgb(COLORS['token'])
            )

            # Highlight the newest token with glow effect
            if i == visible_tokens - 1:
                for offset in [4, 2]:
                    alpha = 100 if offset == 4 else 180
                    draw.rectangle(
                        [x - offset, current_y - offset, x + token_box_width + offset, current_y + token_box_height + offset],
                        outline=hex_to_rgb(COLORS['highlight']),
                        width=1
                    )
        else:
            # Draw empty placeholder
            draw.rectangle(
                [x, current_y, x + token_box_width, current_y + token_box_height],
                fill=hex_to_rgb(COLORS['bg']),
                outline=hex_to_rgb(COLORS['border']),
                width=1
            )

    # Calculate rows used for tokens
    num_rows = (len(tokens) + tokens_per_row - 1) // tokens_per_row
    y += num_rows * (token_box_height + 8) + 15

    # Separator
    draw.line([(padding, y), (width - padding, y)], fill=hex_to_rgb(COLORS['border']), width=1)
    y += 15

    # Output section
    draw.text((padding, y), "Decoded JSON:", font=font_small, fill=hex_to_rgb(COLORS['text_dim']))
    y += 22

    # Draw decoded JSON
    if decoded_json:
        draw_json_colored(draw, padding, y, decoded_json, font, width - 2 * padding)
    else:
        draw.text((padding, y), "(waiting for tokens...)", font=font,
                  fill=hex_to_rgb(COLORS['text_dim']))

    # Stats bar at bottom
    stats_y = height - 45
    draw.line([(padding, stats_y - 10), (width - padding, stats_y - 10)], fill=hex_to_rgb(COLORS['border']), width=1)

    # Draw compression comparison
    if visible_tokens > 0 and utf8_byte_count > 0:
        compression = utf8_byte_count / visible_tokens
        stats_text = f"{utf8_byte_count} bytes → {visible_tokens} tokens ({compression:.1f}x compression)"
    else:
        stats_text = f"? bytes → ? tokens"

    draw.text((padding, stats_y), stats_text, font=font_small, fill=hex_to_rgb(COLORS['text_dim']))

    # Progress bar
    progress_y = height - 18
    progress_width = width - 2 * padding
    progress = visible_tokens / len(tokens) if tokens else 0

    # Background
    draw.rectangle(
        [padding, progress_y, padding + progress_width, progress_y + 6],
        fill=hex_to_rgb(COLORS['token_bg'])
    )
    # Fill
    if progress > 0:
        draw.rectangle(
            [padding, progress_y, padding + int(progress_width * progress), progress_y + 6],
            fill=hex_to_rgb(COLORS['token'])
        )

    return img


def draw_json_colored(draw: ImageDraw.Draw, x: int, y: int, json_str: str, font: ImageFont.FreeTypeFont, max_width: int = 650):
    """Draw JSON with syntax highlighting, with word wrap."""
    lines = []
    current_line = []
    current_line_width = 0

    # First, tokenize the JSON into colored segments
    segments = []
    in_string = False
    in_key = False
    escape_next = False
    current_text = []
    current_color = COLORS['text']

    def flush_segment():
        nonlocal current_text
        if current_text:
            text = ''.join(current_text)
            segments.append((text, current_color))
            current_text = []

    for i, char in enumerate(json_str):
        if escape_next:
            current_text.append(char)
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            current_text.append(char)
            continue

        if char == '"':
            if not in_string:
                flush_segment()
                in_string = True
                rest = json_str[i+1:]
                colon_pos = rest.find(':')
                quote_pos = rest.find('"')
                in_key = colon_pos != -1 and (quote_pos == -1 or colon_pos < quote_pos + 1)
                current_color = COLORS['json_key'] if in_key else COLORS['json_value']
                current_text.append(char)
            else:
                current_text.append(char)
                flush_segment()
                in_string = False
                in_key = False
                current_color = COLORS['text']
        elif char in '{}[]':
            flush_segment()
            current_color = COLORS['json_bracket']
            current_text.append(char)
            flush_segment()
            current_color = COLORS['text']
        elif not in_string and char in ':,':
            flush_segment()
            current_color = COLORS['text_dim']
            current_text.append(char)
            flush_segment()
            current_color = COLORS['text']
        else:
            current_text.append(char)

    flush_segment()

    # Now draw segments, wrapping if needed
    cursor_x = x
    cursor_y = y
    line_height = 18

    for text, color in segments:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        # Check if we need to wrap
        if cursor_x + text_width > x + max_width and cursor_x > x:
            cursor_x = x + 20  # Indent continuation
            cursor_y += line_height

        draw.text((cursor_x, cursor_y), text, font=font, fill=hex_to_rgb(color))
        cursor_x += text_width

    return cursor_y - y + line_height  # Return height used


def generate_animation(
    json_str: str,
    tokens: list,
    decoded_states: list,
    output_path: str,
    width: int = 700,
    height: int = 350,
    frame_duration: int = 800,  # ms per frame
):
    """Generate the animated GIF."""

    font = get_font(14)
    font_small = get_font(12)
    font_title = get_font(18)

    frames = []

    # Initial frame (no tokens)
    frame = create_frame(
        width, height,
        "Type-Constrained Tokenization (TCT)",
        json_str,
        tokens,
        0,
        "",
        "",
        font, font_small, font_title,
        0  # No bytes decoded yet
    )
    frames.append(frame)

    # One frame per token
    for i, (decoded, token) in enumerate(decoded_states):
        decoded_bytes = len(decoded.encode('utf-8')) if decoded else 0
        frame = create_frame(
            width, height,
            "Type-Constrained Tokenization (TCT)",
            json_str,
            tokens,
            i + 1,
            decoded or "{}",
            "",
            font, font_small, font_title,
            decoded_bytes
        )
        frames.append(frame)

    # Final frame (hold longer) - same as last but will be held
    final_decoded = decoded_states[-1][0] if decoded_states else "{}"
    final_bytes = len(final_decoded.encode('utf-8')) if final_decoded else 0
    frame = create_frame(
        width, height,
        "Type-Constrained Tokenization (TCT)",
        json_str,
        tokens,
        len(tokens),
        final_decoded,
        "",
        font, font_small, font_title,
        final_bytes
    )
    frames.append(frame)

    # Save as GIF
    durations = [frame_duration] * (len(frames) - 1) + [frame_duration * 3]  # Hold last frame longer

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0  # Loop forever
    )

    return len(frames)


def main():
    parser = argparse.ArgumentParser(description="Generate TCT animation GIF")
    parser.add_argument("--json", type=str, default='{"apiVersion": "v1", "kind": "Pod"}',
                        help="JSON string to tokenize")
    parser.add_argument("--output", "-o", type=str, default="tct_animation.gif",
                        help="Output GIF file")
    parser.add_argument("--width", type=int, default=700, help="GIF width")
    parser.add_argument("--height", type=int, default=350, help="GIF height")
    parser.add_argument("--speed", type=int, default=800, help="Frame duration in ms")
    args = parser.parse_args()

    # Import TCT
    try:
        import tct_kubernetes_bpe_1k as tct
    except ImportError:
        print("Error: Could not import tct_kubernetes_bpe_1k")
        print("Make sure you've activated the venv.")
        return 1

    # Encode
    tokens = list(tct.encode(args.json))

    # Get decoded states at each step
    decoded_states = []
    for i in range(len(tokens)):
        prefix = tokens[:i+1]
        decoded, consumed, surplus = tct.decode_prefix(prefix)
        decoded_states.append((decoded, tokens[i]))

    # Generate GIF
    num_frames = generate_animation(
        args.json,
        tokens,
        decoded_states,
        args.output,
        args.width,
        args.height,
        args.speed
    )

    print(f"Generated {args.output}")
    print(f"  Input: {args.json}")
    print(f"  Tokens: {tokens}")
    print(f"  Frames: {num_frames}")
    print(f"  Compression: {len(args.json)} bytes → {len(tokens)} tokens ({len(args.json)/len(tokens):.1f}x)")

    return 0


if __name__ == "__main__":
    exit(main())
