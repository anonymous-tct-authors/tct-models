#!/usr/bin/env python3
"""
Animated visualization of TCT (Type-Constrained Tokenization) encoding/decoding.

This script demonstrates how TCT tokenization works by showing:
1. Tokens being added one by one
2. The JSON structure being progressively decoded
3. Visual comparison of token efficiency

Usage:
    python animate_tct.py
    python animate_tct.py --fast
    python animate_tct.py --json '{"apiVersion": "v1", "kind": "Pod"}'
"""

import argparse
import sys
import time
import json

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_BLACK = "\033[40m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


def clear_line():
    """Clear current line."""
    print("\033[2K\r", end="")


def move_up(n=1):
    """Move cursor up n lines."""
    print(f"\033[{n}A", end="")


def clear_screen():
    """Clear screen and move to top."""
    print("\033[2J\033[H", end="")


def print_header(title):
    """Print a styled header."""
    width = 70
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * width}{Colors.RESET}\n")


def print_box(content, title="", width=70):
    """Print content in a box."""
    lines = content.split('\n')

    # Top border
    if title:
        padding = width - len(title) - 4
        print(f"┌─ {Colors.BOLD}{title}{Colors.RESET} {'─' * padding}┐")
    else:
        print(f"┌{'─' * width}┐")

    # Content
    for line in lines:
        # Truncate if needed
        visible_len = len(line.encode('utf-8').decode('utf-8', errors='ignore'))
        if visible_len > width - 4:
            line = line[:width-7] + "..."
        padding = width - 4 - len(line)
        print(f"│  {line}{' ' * max(0, padding)}  │")

    # Bottom border
    print(f"└{'─' * width}┘")


def colorize_json(json_str, highlight_new=""):
    """Add colors to JSON structure with optional new content highlighting."""
    result = []
    in_string = False
    in_key = False
    escape_next = False

    for i, char in enumerate(json_str):
        if escape_next:
            result.append(char)
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            result.append(char)
            continue

        if char == '"':
            if not in_string:
                in_string = True
                # Determine if this is a key (followed by :)
                rest = json_str[i+1:]
                colon_pos = rest.find(':')
                quote_pos = rest.find('"')
                in_key = colon_pos != -1 and (quote_pos == -1 or colon_pos < quote_pos + 1)
                if in_key:
                    result.append(f"{Colors.CYAN}{char}")
                else:
                    result.append(f"{Colors.GREEN}{char}")
            else:
                result.append(f"{char}{Colors.RESET}")
                in_string = False
                in_key = False
        elif char in '{}[]':
            result.append(f"{Colors.YELLOW}{char}{Colors.RESET}")
        elif char in ':,':
            result.append(f"{Colors.DIM}{char}{Colors.RESET}")
        elif not in_string and char in 'truefalsnul':  # keywords
            result.append(f"{Colors.MAGENTA}{char}{Colors.RESET}")
        else:
            result.append(char)

    return ''.join(result)


def animate_encoding(tct, json_str, delay=0.3):
    """Animate the encoding process."""
    print_header("TCT Tokenization Animation")

    # Show input
    print(f"{Colors.BOLD}Input JSON:{Colors.RESET}")
    formatted = json.dumps(json.loads(json_str), indent=2)
    print(colorize_json(formatted))
    print()

    # Get tokens
    tokens = tct.encode(json_str)

    print(f"{Colors.BOLD}Encoding to {len(tokens)} tokens...{Colors.RESET}\n")
    time.sleep(delay)

    # Animate token-by-token decoding
    prev_decoded = ""
    token_displays = []

    for i, token in enumerate(tokens):
        prefix_tokens = list(tokens[:i+1])
        decoded, consumed, surplus = tct.decode_prefix(prefix_tokens)

        # Find what's new
        if decoded != prev_decoded:
            new_content = decoded
        else:
            new_content = ""

        # Display token
        token_str = f"{Colors.BRIGHT_BLUE}{token:4d}{Colors.RESET}"
        token_displays.append(token_str)

        # Clear and redraw
        clear_screen()
        print_header("TCT Tokenization Animation")

        # Show tokens so far
        print(f"{Colors.BOLD}Tokens ({i+1}/{len(tokens)}):{Colors.RESET}")
        tokens_line = " ".join(f"{t:4d}" for t in tokens[:i+1])
        print(f"  [{Colors.CYAN}{tokens_line}{Colors.RESET}]")
        print()

        # Show current decoded state
        print(f"{Colors.BOLD}Decoded JSON:{Colors.RESET}")
        if decoded:
            try:
                formatted = json.dumps(json.loads(decoded), indent=2)
                print(colorize_json(formatted))
            except:
                print(colorize_json(decoded))
        else:
            print(f"{Colors.DIM}(building...){Colors.RESET}")

        # Show what this token added
        if new_content and new_content != prev_decoded:
            print(f"\n{Colors.BRIGHT_GREEN}✓ Token {token} produced output{Colors.RESET}")
        else:
            print(f"\n{Colors.DIM}○ Token {token} (buffered){Colors.RESET}")

        prev_decoded = decoded
        time.sleep(delay)

    # Final summary
    print(f"\n{Colors.BOLD}{'─' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}Summary:{Colors.RESET}")
    print(f"  • Input bytes:  {len(json_str)}")
    print(f"  • TCT tokens:   {len(tokens)}")
    print(f"  • Compression:  {len(json_str)/len(tokens):.1f}x")
    print(f"  • Vocab size:   {tct.vocab_size()}")


def animate_comparison(tct, json_str, delay=0.2):
    """Show a side-by-side comparison animation."""
    print_header("TCT vs UTF-8 Comparison")

    tokens = tct.encode(json_str)
    utf8_tokens = list(json_str.encode('utf-8'))

    # Input
    print(f"{Colors.BOLD}Input:{Colors.RESET} {colorize_json(json_str)}\n")

    # Stats comparison
    print(f"┌{'─'*30}┬{'─'*30}┐")
    print(f"│ {Colors.CYAN}TCT Tokens{Colors.RESET}{' '*19}│ {Colors.YELLOW}UTF-8 Bytes{Colors.RESET}{' '*18}│")
    print(f"├{'─'*30}┼{'─'*30}┤")
    print(f"│ Count: {Colors.BOLD}{len(tokens):4d}{Colors.RESET}{' '*18}│ Count: {Colors.BOLD}{len(utf8_tokens):4d}{Colors.RESET}{' '*17}│")
    print(f"│ Vocab: {Colors.BOLD}{tct.vocab_size():4d}{Colors.RESET}{' '*18}│ Vocab: {Colors.BOLD} 256{Colors.RESET}{' '*17}│")
    print(f"└{'─'*30}┴{'─'*30}┘")

    compression = len(utf8_tokens) / len(tokens)
    print(f"\n{Colors.BOLD}Compression ratio: {Colors.GREEN}{compression:.1f}x{Colors.RESET}")

    # Animate token sequence building
    print(f"\n{Colors.BOLD}TCT Token Sequence:{Colors.RESET}")
    for i in range(len(tokens)):
        token_line = " ".join(f"{t:3d}" for t in tokens[:i+1])
        print(f"\r  [{Colors.CYAN}{token_line}{Colors.RESET}]", end="", flush=True)
        time.sleep(delay)
    print()

    print(f"\n{Colors.BOLD}UTF-8 Byte Sequence:{Colors.RESET}")
    for i in range(0, len(utf8_tokens), 10):
        chunk = utf8_tokens[:i+10]
        byte_line = " ".join(f"{b:3d}" for b in chunk)
        print(f"\r  [{Colors.YELLOW}{byte_line}{Colors.RESET}]", end="", flush=True)
        time.sleep(delay / 5)
    print("\n")


def interactive_demo(tct):
    """Interactive demo mode."""
    print_header("TCT Interactive Demo")

    # Valid Kubernetes manifest examples
    examples = [
        '{"apiVersion": "v1", "kind": "Pod"}',
        '{"apiVersion": "v1", "kind": "Service"}',
        '{"apiVersion": "apps/v1", "kind": "Deployment"}',
        '{"apiVersion": "v1", "kind": "ConfigMap"}',
        '{"apiVersion": "v1", "kind": "Secret"}',
    ]

    print(f"{Colors.BOLD}Example Kubernetes manifests:{Colors.RESET}\n")

    for i, example in enumerate(examples):
        try:
            tokens = tct.encode(example)
            utf8_len = len(example.encode('utf-8'))
            compression = utf8_len / len(tokens)

            print(f"{Colors.CYAN}{i+1}.{Colors.RESET} {colorize_json(example)}")
            print(f"   {Colors.DIM}→ {len(tokens)} tokens (from {utf8_len} bytes, {compression:.1f}x compression){Colors.RESET}")
            print()
        except Exception as e:
            print(f"{Colors.CYAN}{i+1}.{Colors.RESET} {colorize_json(example)}")
            print(f"   {Colors.RED}→ Error: {e}{Colors.RESET}")
            print()


def animate_streaming(tct, json_str, delay=0.05):
    """Non-clearing streaming animation (good for recording)."""
    print_header("TCT Tokenization - Streaming View")

    # Show input
    print(f"{Colors.BOLD}Input:{Colors.RESET} {colorize_json(json_str)}\n")

    tokens = tct.encode(json_str)
    print(f"{Colors.BOLD}Encoding to {len(tokens)} tokens:{Colors.RESET} ", end="", flush=True)

    # Show tokens appearing
    for token in tokens:
        print(f"{Colors.CYAN}{token}{Colors.RESET} ", end="", flush=True)
        time.sleep(delay)
    print("\n")

    # Now show decoding progress
    print(f"{Colors.BOLD}Progressive decoding:{Colors.RESET}\n")

    prev_decoded = ""
    for i, token in enumerate(tokens):
        prefix_tokens = list(tokens[:i+1])
        decoded, consumed, surplus = tct.decode_prefix(prefix_tokens)

        if decoded != prev_decoded:
            # Show the new state
            try:
                formatted = json.dumps(json.loads(decoded), indent=2)
            except:
                formatted = decoded

            print(f"  {Colors.BRIGHT_BLUE}+token {token:4d}{Colors.RESET} → ", end="")

            # Highlight what's new
            if prev_decoded and decoded.startswith(prev_decoded.rstrip('}')):
                # Show delta
                print(f"{Colors.GREEN}{formatted}{Colors.RESET}")
            else:
                print(colorize_json(formatted).replace('\n', '\n' + ' ' * 17))
        else:
            print(f"  {Colors.DIM}+token {token:4d} → (buffered, awaiting more tokens){Colors.RESET}")

        prev_decoded = decoded
        time.sleep(delay * 2)

    print()
    print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}Final:{Colors.RESET} {len(json_str)} bytes → {len(tokens)} tokens ({len(json_str)/len(tokens):.1f}x compression)")


def animate_rich(tct, json_str, delay=0.15):
    """Rich animation showing token meaning."""
    print_header("TCT Token Analysis")

    tokens = tct.encode(json_str)

    print(f"{Colors.BOLD}Input:{Colors.RESET} {colorize_json(json_str)}")
    print(f"{Colors.DIM}({len(json_str)} bytes){Colors.RESET}\n")

    print(f"{Colors.BOLD}Token breakdown:{Colors.RESET}\n")

    prev_decoded = ""
    for i, token in enumerate(tokens):
        prefix_tokens = list(tokens[:i+1])
        decoded, consumed, surplus = tct.decode_prefix(prefix_tokens)

        # Determine what this token represents
        if decoded != prev_decoded:
            delta = decoded if not prev_decoded else "[structural change]"
            status = f"{Colors.GREEN}✓{Colors.RESET}"
            meaning = f"produces: {colorize_json(decoded)[:50]}"
        else:
            status = f"{Colors.YELLOW}○{Colors.RESET}"
            meaning = f"{Colors.DIM}buffered (part of multi-token sequence){Colors.RESET}"

        print(f"  {status} Token {Colors.CYAN}{token:4d}{Colors.RESET} │ {meaning}")
        prev_decoded = decoded
        time.sleep(delay)

    print()

    # Show the full progression as a compact diagram
    print(f"{Colors.BOLD}Token sequence:{Colors.RESET}")
    token_str = " → ".join(f"{Colors.CYAN}{t}{Colors.RESET}" for t in tokens)
    print(f"  {token_str}")

    print()
    print(f"{Colors.BOLD}Compression:{Colors.RESET} {len(json_str)} bytes → {len(tokens)} tokens = {Colors.GREEN}{len(json_str)/len(tokens):.1f}x{Colors.RESET}")


def main():
    parser = argparse.ArgumentParser(description="Animate TCT tokenization")
    parser.add_argument("--fast", action="store_true", help="Fast animation")
    parser.add_argument("--json", type=str, help="Custom JSON to tokenize")
    parser.add_argument("--compare", action="store_true", help="Show comparison with UTF-8")
    parser.add_argument("--demo", action="store_true", help="Show interactive demo")
    parser.add_argument("--stream", action="store_true", help="Streaming animation (no screen clear)")
    parser.add_argument("--rich", action="store_true", help="Rich token analysis")
    args = parser.parse_args()

    # Import TCT
    try:
        import tct_kubernetes_bpe_1k as tct
        print(f"{Colors.DIM}Using tct_kubernetes_bpe_1k (vocab size: {tct.vocab_size()}){Colors.RESET}")
    except ImportError:
        print(f"{Colors.RED}Error: Could not import tct_kubernetes_bpe_1k{Colors.RESET}")
        print("Make sure you've activated the venv and installed the TCT wheel.")
        sys.exit(1)

    delay = 0.1 if args.fast else 0.3

    json_str = args.json or '{"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "test"}}'

    if args.demo:
        interactive_demo(tct)
    elif args.compare:
        animate_comparison(tct, json_str, delay)
    elif args.stream:
        animate_streaming(tct, json_str, delay)
    elif args.rich:
        animate_rich(tct, json_str, delay)
    else:
        animate_encoding(tct, json_str, delay)


if __name__ == "__main__":
    main()
