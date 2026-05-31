# Versioning & Release Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automated versioning, CHANGELOG, and GitHub Releases to `copier-template` using `python-semantic-release` v10 triggered on every push to `main`.

**Architecture:** `python-semantic-release` (already added as a dev dep) reads conventional commits since the last git tag, bumps `pyproject.toml:project.version`, writes `CHANGELOG.md`, pushes a version-bump commit + tag back to `main`, and creates a GitHub Release. A new `release.yml` GitHub Actions workflow drives this on every push to `main`. If no releasable commits land (e.g. only `docs:` or `chore:`), the tool exits cleanly with no release.

**Tech Stack:** `python-semantic-release>=10.5.3`, `uv`, GitHub Actions

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `pyproject.toml` | Modify | Add `[tool.semantic_release]` config blocks |
| `.github/workflows/release.yml` | Create | CI workflow that runs semantic-release on pushes to `main` |
| `uv.lock` | Already modified | Updated by `uv add --dev python-semantic-release` |

---

### Task 1: Commit the dependency addition

`python-semantic-release>=10.5.3` was already added to `[dependency-groups].dev` via `uv add`. Stage and commit the resulting changes.

**Files:**
- Modify (stage): `pyproject.toml`
- Modify (stage): `uv.lock`

- [ ] **Step 1: Verify the dep appears in pyproject.toml**

Run:
```bash
grep "python-semantic-release" pyproject.toml
```
Expected output:
```
    "python-semantic-release>=10.5.3",
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add python-semantic-release dev dependency"
```

---

### Task 2: Configure `python-semantic-release` in `pyproject.toml`

Add the semantic-release configuration blocks to `pyproject.toml`. These tell semantic-release where the version lives, which commits trigger which bump level, where to write the changelog, and that this is a GitHub remote.

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Append the configuration blocks to `pyproject.toml`**

Add the following at the end of `pyproject.toml`:

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]

[tool.semantic_release.branches.main]
match = "main"
prerelease = false

[tool.semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[tool.semantic_release.commit_parser_options]
allowed_tags = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore", "build", "ci"]
minor_tags = ["feat"]
patch_tags = ["fix", "perf", "refactor"]

[tool.semantic_release.remote]
type = "github"

[tool.semantic_release.publish]
upload_to_vcs_release = true
```

**Key choices explained:**
- `version_toml` — tells semantic-release to read/write the version from `project.version` inside `pyproject.toml`
- `branches.main.match = "main"` — only releases from the `main` branch (not feature branches or PRs)
- `patch_tags` includes `refactor` — refactors visible in the changelog and worth a patch bump
- `build_command` is omitted (defaults to `null`) — this repo is a Copier template, nothing to build/publish to PyPI
- `upload_to_vcs_release = true` — attaches any dist files to the GitHub Release (none here, but harmless)

- [ ] **Step 2: Verify the config loads correctly**

Run:
```bash
uv run semantic-release version --print
```
Expected output (a version string like `0.2.0` or `1.0.0`, with a WARNING about a missing token — that warning is expected locally):
```
[HH:MM:SS] WARNING  Token value is missing!  config.py:...
0.2.0
```
If you see `Error: ...` (not WARNING), the config has a problem — re-check the TOML syntax.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "build: configure python-semantic-release"
```

---

### Task 3: Create the release GitHub Actions workflow

Create `.github/workflows/release.yml`. This workflow runs on every push to `main`, installs deps, and delegates to `semantic-release version` + `semantic-release publish`. The `concurrency` key prevents two rapid pushes from creating a race condition on the tag.

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create the workflow file**

Create `.github/workflows/release.yml` with this exact content:

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

**Why `fetch-depth: 0`:** Without the full git history, semantic-release cannot find the previous tag and will compute the wrong next version. This is the most common misconfiguration.

**Why two steps (`version` then `publish`):** `version` handles the commit, tag, and push. `publish` creates the GitHub Release from that tag. Splitting them makes failures easier to diagnose.

- [ ] **Step 2: Validate the YAML syntax**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('YAML OK')"
```
Expected:
```
YAML OK
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: add automated release workflow"
```

---

### Task 4: Create the initial `v0.1.0` tag

Without an existing tag, semantic-release will start at `v1.0.0` (because `feat:` commits in history trigger a minor bump from zero). The spec requires starting at `v0.1.0`. Create that tag manually now — all future releases will increment from here.

**Files:** none (git tag only)

- [ ] **Step 1: Create the tag locally**

```bash
git tag v0.1.0
```

- [ ] **Step 2: Verify the tag exists**

```bash
git tag --list
```
Expected to include:
```
v0.1.0
```

- [ ] **Step 3: Verify `--print` now shows the next version correctly**

```bash
uv run semantic-release version --print
```
Expected: a version like `0.2.0` (if unreleased `feat:` commits exist since the tag) or `0.1.1` (if only `fix:` commits), or the same `0.1.0` with no new release (if no releasable commits since the tag). A WARNING about the token is expected.

- [ ] **Step 4: Push the tag and all pending commits to remote**

```bash
git push && git push --tags
```
Expected: both the branch commits and the `v0.1.0` tag appear on the remote.

- [ ] **Step 5: Verify on GitHub**

Go to the repository's **Tags** page on GitHub and confirm `v0.1.0` appears. The release workflow will NOT fire for this tag (it was pushed directly, not created by semantic-release) — that is correct.
