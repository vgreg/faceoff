"""Command-line interface for faceoff."""

import sys


def main() -> int:
    """Main entry point for the faceoff CLI."""
    from faceoff.app import FaceoffApp

    app = FaceoffApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
