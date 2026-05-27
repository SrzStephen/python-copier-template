# TODO Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement every item in TODO.md — correctness bugs, template hygiene, CI improvements, test infrastructure refactoring, and new tests.

**Architecture:** Work in four passes: (1) test infrastructure refactoring (create `tests/_helpers.py`, update fixtures, add new tests), (2) template correctness fixes (devcontainer pins, uv sync flags, image tag, gitignore, README), (3) meta-repo hygiene (copier.yml, README, prek, CI, LICENSE, justfile), (4) verify full test suite passes. Template changes are tested by the existing + new tests; test infra changes are verified by running the suite after each task.

**Tech Stack:** Python, copier, pytest, prek, Jinja2, just

---

## File Map

**Create:**
- `tests/_helpers.py` — DEFAULTS, devcontainer_variants, _render, _copy, TEMPLATE_ROOT
- `LICENSE` — MIT license for meta-repo
- `template/LICENSE.jinja` — MIT license template for generated projects

**Modify:**
- `tests/conftest.py` — replace devcontainer_variants with docker_available session fixture
- `tests/test_devcontainer_syntax_when_rendered.py` — use _helpers, add use_docker_in_docker param
- `tests/test_devcontainer_build.py` — use _helpers, use docker_available fixture
- `tests/test_template.py` — use _helpers, add 5 new tests, parametrize python version test
- `template/.devcontainer/devcontainer.json.jinja` — feature pins, image tag
- `template/.devcontainer/post-create.sh` — uv sync --all-groups
- `template/justfile.jinja` — uv sync --all-groups, add terraform-check recipe
- `template/pyproject.toml.jinja` — add prek to dev deps
- `template/README.md.jinja` — just prek, remove dangling text
- `template/.gitignore` — remove duplicate block, remove uv.lock line
- `template/prek.toml` — bump ruff to v0.11.13
- `template/.github/workflows/ci.yml.jinja` — setup-uv@v6, prek step
- `copier.yml` — _min_copier_version, validators, cuda note, remove renovate ref
- `README.md` — file tree, questions table
- `prek.toml` — bump ruff to v0.11.13
- `justfile` — add lint recipe

**Delete:**
- `src/` (empty directory at repo root)
- `docs/plans/` (empty directory at repo root)

---

### Task 1: Create `tests/_helpers.py`

**Files:**
- Create: `tests/_helpers.py`

- [ ] **Step 1: Write `tests/_helpers.py`**

```python
"""Shared test utilities — DEFAULTS, helpers, and parametrize decorators."""

from pathlib import Path

import copier
import json5
import pytest

TEMPLATE_ROOT = Path(__file__).parent.parent

DEFAULTS: dict = {
    "project_name": "My Tool",
    "description": "A handy tool for doing things",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "github_username": "testuser",
    "python_version": "3.13",
}

devcontainer_variants = pytest.mark.parametrize(
    "use_terraform,use_cuda,use_aws,use_azure,use_docker_in_docker",
    [
        pytest.param(False, False, False, False, False, id="base"),
        pytest.param(True,  False, False, False, False, id="terraform"),
        pytest.param(False, True,  False, False, False, id="cuda",         marks=pytest.mark.slow),
        pytest.param(False, False, True,  False, False, id="aws"),
        pytest.param(False, False, False, True,  False, id="azure"),
        pytest.param(True,  False, True,  False, False, id="terraform+aws"),
        pytest.param(False, True,  False, False, True,  id="cuda+dind",    marks=pytest.mark.slow),
    ],
)


def _render(tmp_path: Path, extra_data: dict | None = None) -> dict:
    """Render the template and return the parsed devcontainer.json."""
    copier.run_copy(
        str(TEMPLATE_ROOT),
        tmp_path,
        data={**DEFAULTS, **(extra_data or {})},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    content = (tmp_path / ".devcontainer/devcontainer.json").read_text()
    return json5.loads(content)


def _copy(tmp_path: Path, extra_data: dict) -> None:
    """Render the template to tmp_path."""
    copier.run_copy(
        str(TEMPLATE_ROOT),
        tmp_path,
        data={**DEFAULTS, **extra_data},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
```

- [ ] **Step 2: Verify it imports cleanly**

```bash
cd /workspaces/copier-template && python -c "from tests._helpers import DEFAULTS, devcontainer_variants, _render, _copy, TEMPLATE_ROOT; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add tests/_helpers.py
git commit -m "refactor(tests): add _helpers.py with shared utilities"
```

---

### Task 2: Update `tests/conftest.py`

Replace the module-level `devcontainer_variants` decorator with a session-scoped `docker_available` fixture. The decorator moves to `_helpers.py`; conftest gains the fixture so pytest auto-discovers it.

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Replace conftest.py contents**

```python
import shutil
import subprocess

import pytest


@pytest.fixture(scope="session")
def docker_available() -> None:
    """Skip the test if Docker is not available. Run at most once per session."""
    if shutil.which("docker") is None:
        pytest.skip("docker not installed")
    result = subprocess.run(["docker", "info"], capture_output=True, timeout=10)
    if result.returncode != 0:
        pytest.skip("docker not available")
```

- [ ] **Step 2: Run tests to verify nothing breaks yet**

```bash
cd /workspaces/copier-template && uv run pytest -m "not slow" -q --no-header 2>&1 | tail -5
```

Expected: tests will fail because the 3 test files still import `devcontainer_variants` from `tests.conftest`. That's expected — we fix those in Tasks 3–5.

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "refactor(tests): move docker_available to session fixture in conftest"
```

---

### Task 3: Update `tests/test_devcontainer_syntax_when_rendered.py`

Switch from conftest imports to _helpers, add `use_docker_in_docker` param to all parametrized tests.

**Files:**
- Modify: `tests/test_devcontainer_syntax_when_rendered.py`

- [ ] **Step 1: Update imports and remove duplicated DEFAULTS/_render**

Replace the top of the file (lines 1–34) with:

```python
"""Tests that the rendered devcontainer.json has correct syntax and structure."""

from pathlib import Path

import pytest

from tests._helpers import DEFAULTS, TEMPLATE_ROOT, _render, devcontainer_variants
```

Remove the `DEFAULTS` dict definition and the `_render` function definition entirely.

- [ ] **Step 2: Update all `@devcontainer_variants` test signatures**

Every function decorated with `@devcontainer_variants` gains `use_docker_in_docker: bool` as the last parameter, and passes it to `_render`. There are 6 such functions. Pattern for each:

```python
# Before:
@devcontainer_variants
def test_required_top_level_keys_present(
    tmp_path: Path, use_terraform: bool, use_cuda: bool, use_aws: bool, use_azure: bool
) -> None:
    config = _render(
        tmp_path,
        {
            "use_terraform": use_terraform,
            "use_cuda": use_cuda,
            "use_aws": use_aws,
            "use_azure": use_azure,
        },
    )

# After:
@devcontainer_variants
def test_required_top_level_keys_present(
    tmp_path: Path, use_terraform: bool, use_cuda: bool, use_aws: bool, use_azure: bool,
    use_docker_in_docker: bool,
) -> None:
    config = _render(
        tmp_path,
        {
            "use_terraform": use_terraform,
            "use_cuda": use_cuda,
            "use_aws": use_aws,
            "use_azure": use_azure,
            "use_docker_in_docker": use_docker_in_docker,
        },
    )
```

Apply the same change to all 7 `@devcontainer_variants` functions:
- `test_required_top_level_keys_present`
- `test_extensions_is_list_of_strings`
- `test_no_duplicate_extensions`
- `test_features_is_dict_of_dicts`
- `test_mounts_is_list_of_strings`
- `test_forward_ports_is_list_of_ints`
- `test_vscode_settings_has_required_keys`

- [ ] **Step 3: Run this test file to verify**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_devcontainer_syntax_when_rendered.py -m "not slow" -q --no-header 2>&1 | tail -10
```

Expected: all tests pass (same as before, just using shared helpers now)

- [ ] **Step 4: Commit**

```bash
git add tests/test_devcontainer_syntax_when_rendered.py
git commit -m "refactor(tests): use _helpers in test_devcontainer_syntax_when_rendered"
```

---

### Task 4: Update `tests/test_devcontainer_build.py`

Switch to _helpers, replace module-level `docker_available` skipif with the session fixture.

**Files:**
- Modify: `tests/test_devcontainer_build.py`

- [ ] **Step 1: Update imports and top-level definitions**

Replace lines 1–32 with:

```python
"""Tests that the generated devcontainer actually builds via the devcontainer CLI."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tests._helpers import DEFAULTS, TEMPLATE_ROOT, _copy, devcontainer_variants

devcontainer_cli = pytest.mark.skipif(
    shutil.which("devcontainer") is None,
    reason="devcontainer CLI not installed",
)
```

Remove the old `DEFAULTS` dict, `docker_available` skipif mark, and `_copy` function.

- [ ] **Step 2: Update `_build` to use imported `_copy`**

```python
def _build(tmp_path: Path, extra_data: dict) -> subprocess.CompletedProcess:
    _copy(tmp_path, extra_data)
    return subprocess.run(
        ["devcontainer", "build", "--workspace-folder", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=900,
    )
```

- [ ] **Step 3: Update test signatures for `@devcontainer_variants` tests**

Three functions use `@docker_available` and `@devcontainer_variants`. Replace `@docker_available` with `docker_available` as a fixture parameter, and add `use_docker_in_docker`:

```python
# test_devcontainer_builds
@pytest.mark.slow
@devcontainer_cli
@devcontainer_variants
def test_devcontainer_builds(
    docker_available: None,
    tmp_path: Path,
    use_terraform: bool,
    use_cuda: bool,
    use_aws: bool,
    use_azure: bool,
    use_docker_in_docker: bool,
) -> None:
    result = _build(
        tmp_path,
        {
            "use_terraform": use_terraform,
            "use_cuda": use_cuda,
            "use_aws": use_aws,
            "use_azure": use_azure,
            "use_docker_in_docker": use_docker_in_docker,
        },
    )
    assert result.returncode == 0, (
        f"devcontainer build failed (use_terraform={use_terraform}, use_cuda={use_cuda}, "
        f"use_aws={use_aws}, use_azure={use_azure}, use_docker_in_docker={use_docker_in_docker}):\n"
        f"{result.stdout}\n{result.stderr}"
    )


# test_devcontainer_up_invalid_config_fails — add docker_available as fixture param:
@devcontainer_cli
def test_devcontainer_up_invalid_config_fails(docker_available: None, tmp_path: Path) -> None:
    devcontainer_dir = tmp_path / ".devcontainer"
    devcontainer_dir.mkdir()
    (devcontainer_dir / "devcontainer.json").write_text(
        '{"image": "this-image-does-not-exist:never"}'
    )
    result = subprocess.run(
        [
            "devcontainer",
            "up",
            "--workspace-folder",
            str(tmp_path),
            "--remove-existing-container",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0, (
        "devcontainer up should have failed with an invalid image but succeeded"
    )


# test_devcontainer_up
@pytest.mark.slow
@devcontainer_cli
@devcontainer_variants
def test_devcontainer_up(
    docker_available: None,
    tmp_path: Path,
    use_terraform: bool,
    use_cuda: bool,
    use_aws: bool,
    use_azure: bool,
    use_docker_in_docker: bool,
) -> None:
    _copy(
        tmp_path,
        {
            "use_terraform": use_terraform,
            "use_cuda": use_cuda,
            "use_aws": use_aws,
            "use_azure": use_azure,
            "use_docker_in_docker": use_docker_in_docker,
        },
    )
    result = subprocess.run(
        [
            "devcontainer",
            "up",
            "--workspace-folder",
            str(tmp_path),
            "--remove-existing-container",
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert result.returncode == 0, (
        f"devcontainer up failed (use_terraform={use_terraform}, use_cuda={use_cuda}, "
        f"use_aws={use_aws}, use_azure={use_azure}, use_docker_in_docker={use_docker_in_docker}):\n"
        f"{result.stdout}\n{result.stderr}"
    )
```

- [ ] **Step 4: Run (non-slow, non-docker) tests to check imports work**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_devcontainer_build.py -m "not slow" -q --no-header 2>&1 | tail -10
```

Expected: tests are skipped (devcontainer CLI / Docker not available in this environment) but no import errors.

- [ ] **Step 5: Commit**

```bash
git add tests/test_devcontainer_build.py
git commit -m "refactor(tests): use _helpers and docker_available fixture in test_devcontainer_build"
```

---

### Task 5: Update `tests/test_template.py` — use _helpers, add new tests

**Files:**
- Modify: `tests/test_template.py`

- [ ] **Step 1: Update imports and remove duplicated DEFAULTS**

Replace lines 1–22 with:

```python
"""Tests to verify the copier template generates correctly."""

import shutil
import subprocess
from pathlib import Path

import copier
import json5
import pytest

from tests._helpers import DEFAULTS, TEMPLATE_ROOT

TEMPLATE_DIR = TEMPLATE_ROOT / "template"
```

Remove the `DEFAULTS` dict that was defined inline. The `TEMPLATE_ROOT` line that was inline (`TEMPLATE_ROOT = Path(__file__).parent.parent`) is also removed since it now comes from `_helpers`.

- [ ] **Step 2: Replace `test_generated_project_tests_pass` with a parametrized version**

Remove the existing `test_generated_project_tests_pass` function and replace it with:

```python
@pytest.mark.parametrize("python_version", ["3.12", "3.13"])
def test_generated_project_tests_pass(tmp_path: Path, python_version: str) -> None:
    dst = tmp_path / "proj"
    copier.run_copy(
        str(TEMPLATE_ROOT),
        dst,
        data={**DEFAULTS, "python_version": python_version},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    result = subprocess.run(
        ["uv", "run", "pytest", "--no-header", "-q"],
        cwd=dst,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"pytest failed for Python {python_version}:\n{result.stdout}\n{result.stderr}"
    )
```

- [ ] **Step 3: Add `test_cli_entrypoint_runs`**

After `test_generated_project_installs`, add:

```python
def test_cli_entrypoint_runs(generated: Path) -> None:
    result = subprocess.run(
        ["uv", "run", "my-tool", "--help"],
        cwd=generated,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI entrypoint failed:\n{result.stderr}"
```

- [ ] **Step 4: Add `test_copier_answers_file_exists`**

```python
def test_copier_answers_file_exists(generated: Path) -> None:
    import yaml
    answers_file = generated / ".copier-answers.yml"
    assert answers_file.exists(), ".copier-answers.yml was not generated"
    data = yaml.safe_load(answers_file.read_text())
    assert "project_name" in data
    assert "_src_path" in data
```

- [ ] **Step 5: Add `test_copier_update_works`**

```python
def test_copier_update_works(tmp_path: Path) -> None:
    copier.run_copy(
        str(TEMPLATE_ROOT),
        tmp_path,
        data=DEFAULTS,
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    copier.run_update(
        dst_path=str(tmp_path),
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / ".copier-answers.yml").exists()
```

- [ ] **Step 6: Add `test_terraform_validate_passes`**

```python
@pytest.mark.slow
def test_terraform_validate_passes(generated_with_terraform: Path) -> None:
    if shutil.which("terraform") is None:
        pytest.skip("terraform not in PATH")
    result = subprocess.run(
        ["terraform", "init", "-backend=false"],
        cwd=generated_with_terraform / "infra",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"terraform init failed:\n{result.stderr}"
    result = subprocess.run(
        ["terraform", "validate"],
        cwd=generated_with_terraform / "infra",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"terraform validate failed:\n{result.stderr}"
```

- [ ] **Step 7: Run non-slow tests to verify**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_template.py -m "not slow" -q --no-header 2>&1 | tail -15
```

Expected: all non-slow tests pass. `test_copier_answers_file_exists` may need `pyyaml` — if so add it: `uv add --dev pyyaml`

- [ ] **Step 8: Commit**

```bash
git add tests/test_template.py
git commit -m "test: add CLI, copier update, answers file, parametrized python version tests"
```

---

### Task 6: Fix `template/.devcontainer/devcontainer.json.jinja`

Update feature pins to match the parent devcontainer, and render the image tag from `python_version`.

**Files:**
- Modify: `template/.devcontainer/devcontainer.json.jinja`

- [ ] **Step 1: Update docker-in-docker pin**

```
# Before:
{% if use_docker_in_docker %}"ghcr.io/devcontainers/features/docker-in-docker:2": {"moby": false},{% endif %}

# After:
{% if use_docker_in_docker %}"ghcr.io/devcontainers/features/docker-in-docker:3.0.1": {"moby": false},{% endif %}
```

- [ ] **Step 2: Update node pin**

```
# Before:
"ghcr.io/devcontainers/features/node:1": {},

# After:
"ghcr.io/devcontainers/features/node:2.0.0": { "version": 24 },
```

- [ ] **Step 3: Update claude-code feature**

```
# Before:
"ghcr.io/stu-bell/devcontainer-features/claude-code:0": {},

# After:
"ghcr.io/SrzStephen/devcontainer-features/claude-code:1": {
  "marketplace": "https://github.com/obra/superpowers-marketplace",
  "plugin": "superpowers@superpowers-marketplace",
  "removeAttribution": true,
  "statusline": true
},
```

- [ ] **Step 4: Update image tag**

```
# Before:
"image": "mcr.microsoft.com/devcontainers/python:3.12",

# After:
"image": "mcr.microsoft.com/devcontainers/python:{{ python_version.split(',')[0] }}",
```

- [ ] **Step 5: Run devcontainer JSON tests**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_devcontainer_syntax_when_rendered.py -m "not slow" -q --no-header 2>&1 | tail -10
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add template/.devcontainer/devcontainer.json.jinja
git commit -m "fix(devcontainer): update feature pins and render image tag from python_version"
```

---

### Task 7: Fix template runtime files — uv sync, prek dep, terraform-check

**Files:**
- Modify: `template/.devcontainer/post-create.sh`
- Modify: `template/justfile.jinja`
- Modify: `template/pyproject.toml.jinja`

- [ ] **Step 1: Fix `template/.devcontainer/post-create.sh`**

```bash
# Before:
  uv sync --all-extras

# After:
  uv sync --all-groups
```

- [ ] **Step 2: Fix `template/justfile.jinja` — uv sync and add terraform-check**

```
# Before setup recipe:
setup:
    uv sync --all-extras
    uv run prek install

# After:
setup:
    uv sync --all-groups
    uv run prek install
```

Add terraform-check recipe after the existing recipes (use Jinja conditional):

```jinja
{% if use_terraform %}
terraform-check:
    terraform fmt -check infra/
    terraform validate -chdir=infra/
{% endif %}
```

- [ ] **Step 3: Add prek to `template/pyproject.toml.jinja` dev deps**

```toml
# Before:
[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-cov",
    "pytest-mock",
    "pytest-asyncio",
    "ruff",
    "ty",
]

# After:
[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-cov",
    "pytest-mock",
    "pytest-asyncio",
    "prek>=0.1",
    "ruff",
    "ty",
]
```

- [ ] **Step 4: Run template tests to verify**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_template.py::test_expected_files_exist tests/test_template.py::test_pyproject_toml_rendered -q --no-header 2>&1 | tail -5
```

Expected: PASSED

- [ ] **Step 5: Commit**

```bash
git add template/.devcontainer/post-create.sh template/justfile.jinja template/pyproject.toml.jinja
git commit -m "fix(template): use uv sync --all-groups, add prek dev dep, add terraform-check recipe"
```

---

### Task 8: Fix `template/README.md.jinja`

**Files:**
- Modify: `template/README.md.jinja`

- [ ] **Step 1: Fix `just pre-commit` → `just prek`**

```markdown
# Before:
| `just pre-commit`| Run pre-commit on all files       |

# After:
| `just prek`      | Run pre-commit on all files       |
```

- [ ] **Step 2: Remove dangling "The usual steps" text**

Lines 32–34 currently read:
```markdown
## Setup

This repository is set up to run out of a [devcontainer](...) via Visual Studio Code.

The usual steps
```

Remove "The usual steps" and the blank line before it, leaving:
```markdown
## Setup

This repository is set up to run out of a [devcontainer](...) via Visual Studio Code.
```

- [ ] **Step 3: Verify template renders cleanly**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_template.py::test_readme_rendered -q --no-header 2>&1 | tail -5
```

Expected: PASSED

- [ ] **Step 4: Commit**

```bash
git add template/README.md.jinja
git commit -m "fix(template): fix prek recipe name and remove dangling text in README"
```

---

### Task 9: Fix `template/.gitignore`

**Files:**
- Modify: `template/.gitignore`

- [ ] **Step 1: Remove the first duplicate block (lines 1–22)**

The file starts with a short block that duplicates content from line 24 onward. Delete lines 1–22:

```
__pycache__/
*.py[cod]
*$py.class
*.so
build/
dist/
*.egg-info/
.eggs/
.env
.venv/
env/
venv/
.coverage
coverage.xml
htmlcov/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.ty_cache/
*.log
.DS_Store
```

And the two blank lines that follow, leaving the file starting at the `# Byte-compiled / optimized / DLL files` comment.

- [ ] **Step 2: Remove the `uv.lock` line**

Find and delete the line:
```
uv.lock
```

(It's in the `# UV` section, currently around line 102 after the trim above.)

- [ ] **Step 3: Verify template renders cleanly**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_template.py::test_expected_files_exist -q --no-header 2>&1 | tail -5
```

Expected: PASSED

- [ ] **Step 4: Commit**

```bash
git add template/.gitignore
git commit -m "fix(template): remove duplicate gitignore block and stop ignoring uv.lock"
```

---

### Task 10: Update `copier.yml`

**Files:**
- Modify: `copier.yml`

- [ ] **Step 1: Add `_min_copier_version`**

At the very top of `copier.yml`, before `_subdirectory`, add:

```yaml
_min_copier_version: "9.0.0"
```

- [ ] **Step 2: Add `package_name` validator**

```yaml
package_name:
  type: str
  help: "Python package name (snake_case, auto-derived)"
  default: "{{ project_name | lower | replace('-', '_') | replace(' ', '_') }}"
  validator: >-
    {% if not (package_name | regex_search('^[a-z][a-z0-9_]*$')) %}
    package_name must be a valid snake_case Python identifier (lowercase letters, digits, underscores, starting with a letter)
    {% endif %}
```

- [ ] **Step 3: Add `cli_command` validator**

```yaml
cli_command:
  type: str
  help: "CLI command name (e.g. 'mytool')"
  default: "{{ package_name | replace('_', '-') }}"
  validator: >-
    {% if not (cli_command | regex_search('^[a-z][a-z0-9-]*$')) %}
    cli_command must be a valid kebab-case name (lowercase letters, digits, hyphens, starting with a letter)
    {% endif %}
```

- [ ] **Step 4: Update `use_cuda` help text with DID note**

```yaml
use_cuda:
  type: bool
  help: "Requires NVIDIA GPU / CUDA support in the devcontainer? Note: nvidia-container-toolkit is only installed when BOTH use_cuda AND use_docker_in_docker are true."
  default: false
```

- [ ] **Step 5: Remove "renovate" from `github_username` help**

```yaml
github_username:
  type: str
  help: "Your GitHub username (used in CI badges)"
  default: "SrzStephen"
```

- [ ] **Step 6: Verify template copy still works**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_template.py::test_expected_files_exist -q --no-header 2>&1 | tail -5
```

Expected: PASSED

- [ ] **Step 7: Commit**

```bash
git add copier.yml
git commit -m "feat(copier): add min version, validators, cuda/dind note, remove renovate ref"
```

---

### Task 11: Update meta-repo `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the file tree section**

Replace the file tree block (lines ~33–67) with:

```markdown
## Deployed file structure

A few files get added based on your answers:

```zsh
➜  my-new-project tree -a
.
my-new-project
├── .devcontainer
│   ├── devcontainer.json
│   ├── initialize.sh
│   ├── post-create.sh
│   └── post-start.sh
├── .editorconfig
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── workflows
│       ├── ci.yml
│       └── terraform.yml       # only with use_terraform
├── .gitignore
├── .vscode
│   └── settings.json
├── infra                       # only with use_terraform
│   ├── main.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── variables.tf
├── justfile
├── LICENSE
├── prek.toml
├── pyproject.toml
├── README.md
├── src
│   └── mytool
│       ├── cli.py
│       ├── __init__.py
│       └── py.typed
└── tests
    ├── __init__.py
    └── test_cli.py
```
```

- [ ] **Step 2: Add `use_docker_in_docker` to the questions table**

```markdown
| `use_docker_in_docker` | Docker-in-Docker support in devcontainer (default: no) |
```

Add it after the `use_terraform` row.

- [ ] **Step 3: Verify README renders (visual check)**

```bash
grep -n "use_docker_in_docker\|pre-commit-config\|variables.tf\|renovate" /workspaces/copier-template/README.md
```

Expected: `use_docker_in_docker` appears in the table; `pre-commit-config` and stray root `variables.tf` do not appear; `renovate` does not appear.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update README file tree and questions table"
```

---

### Task 12: Bump ruff in prek.toml files

**Files:**
- Modify: `prek.toml`
- Modify: `template/prek.toml`

- [ ] **Step 1: Bump ruff in meta-repo `prek.toml`**

```toml
# Before:
rev = "v0.9.9"

# After:
rev = "v0.11.13"
```

(There is only one ruff entry in prek.toml — the first `[[repos]]` block.)

- [ ] **Step 2: Bump ruff in `template/prek.toml`**

Same change:
```toml
rev = "v0.9.9"  →  rev = "v0.11.13"
```

- [ ] **Step 3: Run prek to verify hooks work with new version**

```bash
cd /workspaces/copier-template && uv run prek run --all-files 2>&1 | tail -20
```

Expected: hooks pass (or only fail on actual code issues, not prek config issues)

- [ ] **Step 4: Commit**

```bash
git add prek.toml template/prek.toml
git commit -m "chore: bump ruff to v0.11.13 in prek.toml files"
```

---

### Task 13: Update template CI workflow

**Files:**
- Modify: `template/.github/workflows/ci.yml.jinja`

- [ ] **Step 1: Bump setup-uv to v6 in all jobs**

There are 3 occurrences of `setup-uv@v5` (in lint, typecheck, and test jobs). Change all to `setup-uv@v6`:

```yaml
# All three occurrences:
- uses: astral-sh/setup-uv@v5
# →
- uses: astral-sh/setup-uv@v6
```

- [ ] **Step 2: Replace standalone ruff steps with prek in the lint job**

```yaml
# Before:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uvx ruff check .
      - run: uvx ruff format --check .

# After:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run prek run --all-files
```

- [ ] **Step 3: Verify the rendered CI file is valid YAML**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_template.py::test_ci_workflow_rendered -q --no-header 2>&1 | tail -5
```

Expected: PASSED

- [ ] **Step 4: Commit**

```bash
git add template/.github/workflows/ci.yml.jinja
git commit -m "fix(template): bump setup-uv to v6 and replace ruff steps with prek in CI"
```

---

### Task 14: Add LICENSE files

**Files:**
- Create: `LICENSE`
- Create: `template/LICENSE.jinja`

- [ ] **Step 1: Create meta-repo `LICENSE`**

```
MIT License

Copyright (c) 2026 Stephen Mott

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Create `template/LICENSE.jinja`**

```jinja
MIT License

Copyright (c) {{ now.year }} {{ author_name }}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Add LICENSE to expected files test**

In `tests/test_template.py`, add `"LICENSE"` to the `expected` list in `test_expected_files_exist`:

```python
expected = [
    "pyproject.toml",
    "justfile",
    ".editorconfig",
    ".gitignore",
    "prek.toml",
    "LICENSE",          # add this line
    ".devcontainer/devcontainer.json",
    ...
]
```

- [ ] **Step 4: Verify**

```bash
cd /workspaces/copier-template && uv run pytest tests/test_template.py::test_expected_files_exist -q --no-header 2>&1 | tail -5
```

Expected: PASSED (the generated project now has a LICENSE file)

- [ ] **Step 5: Commit**

```bash
git add LICENSE template/LICENSE.jinja tests/test_template.py
git commit -m "feat: add MIT LICENSE to meta-repo and template"
```

---

### Task 15: Update meta-repo `justfile` and clean up empty directories

**Files:**
- Modify: `justfile`
- Delete: `src/` (empty directory)
- Delete: `docs/plans/` (empty directory, if present and empty)

- [ ] **Step 1: Add `lint` recipe to `justfile`**

```justfile
prek:
    uv run prek run --all-files

lint:
    uvx ruff check .
    uvx ruff format --check .

test *args:
    uv run pytest -m "not slow" {{args}} -rsx

test-slow *args:
    uv run pytest -m slow {{args}} -rsx
```

- [ ] **Step 2: Delete empty directories**

```bash
# Remove empty src/ at repo root
rmdir /workspaces/copier-template/src 2>/dev/null || echo "src/ already gone or not empty"

# Remove empty docs/plans/ at repo root
rmdir /workspaces/copier-template/docs/plans 2>/dev/null || echo "docs/plans/ already gone or not empty"
```

- [ ] **Step 3: Verify lint recipe works**

```bash
cd /workspaces/copier-template && just lint 2>&1 | tail -5
```

Expected: passes (or shows only actual lint issues)

- [ ] **Step 4: Commit**

```bash
git add justfile
git status  # verify src/ and docs/plans/ show as deleted if they existed
git commit -m "feat(justfile): add lint recipe; remove empty src/ and docs/plans/ directories"
```

---

### Task 16: Run full test suite and verify

- [ ] **Step 1: Run all non-slow tests**

```bash
cd /workspaces/copier-template && uv run pytest -m "not slow" -q --no-header 2>&1 | tail -20
```

Expected: all tests pass

- [ ] **Step 2: Check for any import errors or collection warnings**

```bash
cd /workspaces/copier-template && uv run pytest --collect-only -q 2>&1 | grep -E "ERROR|WARNING" | head -20
```

Expected: no errors

- [ ] **Step 3: Run prek on full codebase**

```bash
cd /workspaces/copier-template && uv run prek run --all-files 2>&1 | tail -30
```

Expected: all hooks pass

- [ ] **Step 4: Final commit if any hook fixes were applied**

```bash
git add -p  # review any auto-fixes from prek
git commit -m "fix: apply prek auto-fixes" 2>/dev/null || echo "nothing to commit"
```

---

## Spec Coverage Check

| Spec item | Task |
|-----------|------|
| Feature pin drift (dind, node, claude-code) | Task 6 |
| Image tag from python_version | Task 6 |
| uv sync --all-groups | Task 7 |
| just prek fix in README.md.jinja | Task 8 |
| Dangling text in README.md.jinja | Task 8 |
| template/.gitignore duplicates + uv.lock | Task 9 |
| copier.yml validators | Task 10 |
| copier.yml _min_copier_version | Task 10 |
| CUDA+DID note in copier.yml | Task 10 |
| Remove renovate ref | Task 10 |
| Meta README file tree | Task 11 |
| Meta README use_docker_in_docker table | Task 11 |
| Ruff bump in prek.toml | Task 12 |
| CI setup-uv v6 | Task 13 |
| CI prek step | Task 13 |
| LICENSE files | Task 14 |
| Meta justfile lint recipe | Task 15 |
| Delete empty dirs | Task 15 |
| DEFAULTS to _helpers | Task 1, 3, 4, 5 |
| _render/_copy to _helpers | Task 1, 3, 4 |
| devcontainer_variants to _helpers | Task 1, 2, 3, 4 |
| Combo variant matrix | Task 1 |
| docker_available session fixture | Task 2, 4 |
| CLI entrypoint test | Task 5 |
| copier answers file test | Task 5 |
| copier update test | Task 5 |
| Parametrize python version test | Task 5 |
| terraform validate test | Task 5 |
| prek dev dep in template | Task 7 |
| terraform-check justfile recipe | Task 7 |
