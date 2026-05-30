#!/bin/bash
set -euo pipefail
if git rev-parse --git-dir &>/dev/null; then
  git config pull.rebase true
  git config rebase.autoStash true
  git config init.defaultBranch main
  git config alias.lg "log --oneline --graph --decorate --all"
  git config alias.change "git log --format=format: --name-only --since='1 year ago' | sort | uniq -c | sort -nr | head -20"
  git config color.ui auto
fi


# The .cache/uv bind mount causes Docker to create /home/vscode/.cache as root-owned.
# Fix ownership so vscode can create subdirectories (e.g. prek).
sudo chown vscode:vscode /home/vscode/.cache

if [ -f pyproject.toml ]; then
  echo "pyproject.toml found, running uv sync..."
  uv sync --all-extras
else
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
