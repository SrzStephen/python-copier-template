#!/bin/bash
set -euo pipefail

# Runs on the *host* before the container is created.
# All paths use ${HOME} (the host user's home directory).
# Files and directories must be created as the host user, not root.

directories=(
  "$HOME/.cache/uv"
  "$HOME/.cache/huggingface"
  "$HOME/.cache/devcontainer"
  "$HOME/.claude"
  "$HOME/.claude/projects"
  "$HOME/.config/gh"
  "$HOME/.npm"
  "$HOME/.cache/pre-commit"
)

files=(
  "$HOME/.claude.json"
)

for dir in "${directories[@]}"; do
  # install -d applies ownership to every component it creates, unlike mkdir -p + chown
  install -d -o "$(id -u)" -g "$(id -g)" "$dir"
done

for file in "${files[@]}"; do
  touch "$file"
  # make sure that these are created with user permissions
  chown "$(id -u):$(id -g)" "$file"
done
