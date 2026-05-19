#!/usr/bin/env python3
"""Validate a TCT syntax-token package for tct-models training handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nanochat.tct_syntax_token_package import check_tct_syntax_token_package


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--write-validate-alias",
        action="store_true",
        help="Copy validation.jsonl to validate.jsonl when the alias is absent.",
    )
    args = parser.parse_args()

    summary = check_tct_syntax_token_package(
        args.package_dir,
        write_validate_alias=args.write_validate_alias,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, sort_keys=True)
            handle.write("\n")

    print(
        "TCT syntax-token package check: "
        f"ok={summary['ok']}, sequences={summary['sequence_count']}, "
        f"errors={len(summary['errors'])}"
    )
    if not summary["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
