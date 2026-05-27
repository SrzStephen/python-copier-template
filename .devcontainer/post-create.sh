#!/bin/bash
set -euo pipefail

# The .cache/uv bind mount causes Docker to create /home/vscode/.cache as root-owned.
# Fix ownership so vscode can create subdirectories (e.g. prek).
sudo chown vscode:vscode /home/vscode/.cache

npm install -g @devcontainers/cli

if [ -f pyproject.toml ]; then
  echo "pyproject.toml found, running uv sync..."
  uv sync --all-extras
  echo "No pyproject.toml found, skipping uv sync."
fi

if [ -f prek.toml ]; then
  if uv pip show prek &>/dev/null; then
    echo "prek config and package found, installing hooks..."
    uv run prek install
  else
    echo "Skipping prek install (prek package not installed)."
  fi
else
  echo "Skipping prek install (no prek.toml found)."
fi
