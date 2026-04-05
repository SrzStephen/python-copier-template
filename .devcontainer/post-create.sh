#!/bin/bash
set -euo pipefail

# The .cache/uv bind mount causes Docker to create /home/vscode/.cache as root-owned.
# Fix ownership so vscode can create subdirectories (e.g. pre-commit).
sudo chown vscode:vscode /home/vscode/.cache

npm install -g @devcontainers/cli

if command -v claude &>/dev/null; then
  echo "Installing superpowers plugin for Claude Code..."
  claude plugin marketplace add obra/superpowers-marketplace
  claude plugin install superpowers@superpowers-marketplace
else
  echo "Skipping superpowers install (claude CLI not found)."
fi


if [ -f pyproject.toml ]; then
  echo "pyproject.toml found, running uv sync..."
  uv sync --all-extras
else
  echo "No pyproject.toml found, skipping uv sync."
fi

if [ -f .pre-commit-config.yaml ]; then
  if uv pip show pre-commit &>/dev/null; then
    echo "pre-commit config and package found, installing hooks..."
    uv run pre-commit install
  else
    echo "Skipping pre-commit install (pre-commit package not installed)."
  fi
else
  echo "Skipping pre-commit install (no .pre-commit-config.yaml found)."
fi
