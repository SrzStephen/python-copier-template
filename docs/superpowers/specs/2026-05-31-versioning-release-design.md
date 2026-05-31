# Versioning & Release Workflow Design

**Date:** 2026-05-31
**Status:** Approved

## Summary

Add automated versioning and releases to the `copier-template` repo using `python-semantic-release`. Every merge to `main` that contains releasable conventional commits automatically bumps the version, updates `CHANGELOG.md`, creates a git tag, and publishes a GitHub Release.

## Architecture

- **Tool:** `python-semantic-release` (dev dependency, invoked via `uv run`)
- **Trigger:** Push to `main` via a new `.github/workflows/release.yml`
- **Version source of truth:** `pyproject.toml:project.version`
- **Changelog:** `CHANGELOG.md` in repo root, also mirrored to GitHub Release body
- **No package publishing:** `build_command = false` — this repo is a Copier template, not a PyPI package

**Flow on each push to `main`:**
1. `semantic-release version` — analyzes commits since last tag, determines bump type, updates `pyproject.toml`, writes `CHANGELOG.md`, commits and pushes the version bump, creates and pushes the git tag
2. `semantic-release publish` — creates a GitHub Release from the tag with changelog as the release body

If no releasable commits are present, both commands exit cleanly with no release produced.

## Conventional Commit → Bump Rules

| Commit type | Version bump |
|---|---|
| `feat:` | minor |
| `fix:`, `perf:`, `refactor:` | patch |
| `BREAKING CHANGE` footer or `!` suffix | major |
| `docs:`, `chore:`, `ci:`, `style:`, `test:`, `build:` | no release |

## Configuration (`pyproject.toml`)

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
branch = "main"
changelog_file = "CHANGELOG.md"
build_command = false

[tool.semantic_release.commit_parser_options]
allowed_tags = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore", "build", "ci"]
minor_tags = ["feat"]
patch_tags = ["fix", "perf", "refactor"]

[tool.semantic_release.remote]
type = "github"

[tool.semantic_release.publish]
upload_to_vcs_release = true
```

## Release Workflow (`.github/workflows/release.yml`)

```yaml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    concurrency: release

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.13"

      - run: uv sync

      - run: uv run semantic-release version
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - run: uv run semantic-release publish
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Key details:**
- `fetch-depth: 0` — full git history required for semantic-release to find the previous tag
- `concurrency: release` — prevents race conditions from two rapid pushes
- `contents: write` — allows pushing the version bump commit and tag back to `main`

## Caveats

- **Branch protection:** If `main` ever gets a "require PR" branch protection rule, `GITHUB_TOKEN` will be blocked from pushing the release commit. The fix is to use a Personal Access Token (PAT) stored as `GH_TOKEN` secret, or to add the release bot as a bypass actor.
- **First release:** The initial tag must be created manually (`git tag v0.1.0 && git push --tags`) or semantic-release will start from `v0.0.0`.

## Out of Scope

- PyPI publishing
- Automatic changelog PR previews
- Release-gating (no "Release PR" review step)
