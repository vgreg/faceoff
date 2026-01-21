#!/usr/bin/env bash
set -e

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/root/.cargo/bin:$PATH"

# Install Dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install --install-hooks
