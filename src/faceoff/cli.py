"""Command-line interface for faceoff."""

import argparse
import sys


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="faceoff",
        description="Terminal TUI for watching NHL hockey games.",
    )
    parser.add_argument(
        "--refresh-interval",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Seconds between auto-refreshes for live games and the schedule (min 5, default 30).",
    )
    args = parser.parse_args(argv)
    if args.refresh_interval < 5:
        parser.error("--refresh-interval must be at least 5 seconds")
    return args


def main() -> int:
    """Main entry point for the faceoff CLI."""
    args = _parse_args()
    from faceoff.app import FaceoffApp

    app = FaceoffApp(refresh_interval=args.refresh_interval)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
