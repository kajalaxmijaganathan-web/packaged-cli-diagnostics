"""Command-line entry point for DevCheck."""
from __future__ import annotations

import argparse
import json
import sys

from .diagnostics import ConfigurationError, format_report, load_config, run_diagnostics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devcheck",
        description="Inspect your machine and report developer-environment health.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--config", help="Path to a JSON configuration file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigurationError as exc:
        print(f"devcheck: configuration error: {exc}", file=sys.stderr)
        return 2

    report = run_diagnostics(config)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_report(report))
    return 1 if report["status"] != "healthy" else 0


if __name__ == "__main__":
    raise SystemExit(main())
