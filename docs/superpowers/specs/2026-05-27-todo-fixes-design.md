# Design: TODO.md Fixes

**Date:** 2026-05-27
**Scope:** All items in TODO.md — correctness bugs, template hygiene, CI, test infrastructure, and new tests.

---

## Section 1: Template correctness

### Devcontainer feature pin drift

`template/.devcontainer/devcontainer.json.jinja` uses stale feature versions. Update to match the parent devcontainer:

| Feature | Current | Target |
|---------|---------|--------|
| docker-in-docker | `2` | `3.0.1` |
| node | `1` | `2.0.0` |
| claude-code provider | `stu-bell` | `SrzStephen` |
| claude-code rev | `0` | `1` |

### Image tag rendering

The `image` field is hardcoded `python:3.12`. Render from the copier variable:
```jinja
"image": "mcr.microsoft.com/devcontainers/python:{{ python_version.split(',')[0] }}"
```

### `uv sync` flags

Both `template/.devcontainer/post-create.sh` and `template/justfile.jinja` use `uv sync --all-extras`.
There are no extras, only dependency groups. Change to `uv sync --all-groups` in both.

### README.md.jinja fixes

- Line 25: `just pre-commit` → `just prek` (the recipe is named `prek`, not `pre-commit`)
- Line 33–34: Remove the dangling "The usual steps" text followed by nothing

### template/.gitignore

- Remove the first 22 lines (a shorter duplicate block; the comprehensive block from line 24 onwards is canonical)
- Remove the `uv.lock` line (line 124): this is an opinionated app template — lockfiles should be committed

### copier.yml

- Add `_min_copier_version: "9.0.0"` at top level
- Add validators for `package_name` and `cli_command` (snake_case and kebab-case patterns respectively)
- Add a note to `use_cuda`'s help text about the Docker-in-Docker interaction:
  > "nvidia-container-toolkit is only installed when BOTH use_cuda AND use_docker_in_docker are true"

### Meta-repo README.md

- Update file tree: remove `.pre-commit-config.yaml` and stray `variables.tf` at root; add `prek.toml`, `.editorconfig`, `.vscode/`
- Add `use_docker_in_docker` row to the questions table
- Remove any references to `renovate.json` (verify by grep — likely a no-op if already deleted)

---

## Section 2: Template hygiene + CI

### Ruff version bumps

`prek.toml` (meta-repo) and `template/prek.toml` both pin ruff to `v0.9.9`. Bump to `v0.11.13`.

### CI workflow (`template/.github/workflows/ci.yml.jinja`)

- Bump `setup-uv@v5` → `setup-uv@v6` in all jobs
- Replace the standalone `uvx ruff check` / `uvx ruff format --check` step with `uv run prek run --all-files` so the same hooks run in CI as locally

### Terraform justfile recipe

When `use_terraform=True`, the generated `justfile.jinja` gets a `terraform-check` recipe:
```justfile
{% if use_terraform %}
terraform-check:
    terraform fmt -check infra/
    terraform validate -chdir=infra/
{% endif %}
```

### LICENSE files

- Add `LICENSE` (MIT) to the meta-repo root (author: Stephen Mott)
- Add `template/LICENSE.jinja` rendered with `{{ author_name }}` and `{{ _copier_conf.now.year }}` (copier's built-in current-year variable) so generated projects have a license

### Meta-repo justfile

Add a `lint` recipe:
```justfile
lint:
    uvx ruff check .
    uvx ruff format --check .
```

### Empty directories

Delete `src/` and `docs/plans/` from the meta-repo root (both empty).

---

## Section 3: Test infrastructure refactoring

### New file: `tests/_helpers.py`

Centralise shared test utilities:

```python
DEFAULTS = {
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
        pytest.param(False, True,  False, False, False, id="cuda",    marks=pytest.mark.slow),
        pytest.param(False, False, True,  False, False, id="aws"),
        pytest.param(False, False, False, True,  False, id="azure"),
        pytest.param(True,  False, True,  False, False, id="terraform+aws"),
        pytest.param(False, True,  False, False, True,  id="cuda+dind", marks=pytest.mark.slow),
    ],
)

def _render(tmp_path, extra_data=None): ...
def _copy(tmp_path, extra_data): ...
```

Remove `DEFAULTS` from `test_template.py`, `test_devcontainer_build.py`, and `test_devcontainer_syntax_when_rendered.py`; import from `_helpers` instead.

Remove the `_render` and `_copy` function definitions from their respective test files; import from `_helpers`.

### `tests/conftest.py`

`devcontainer_variants` is currently a module-level decorator, not a fixture. Move it to `tests/_helpers.py` as a plain constant. `conftest.py` becomes empty (or minimal — session-level fixtures only).

### `tests/test_devcontainer_build.py`: session-scoped `docker_available`

Current code runs `subprocess.run(["docker", "info"])` at module import time (collection phase). Replace with a session-scoped pytest fixture:

```python
@pytest.fixture(scope="session")
def docker_available():
    if shutil.which("docker") is None:
        pytest.skip("Docker not installed")
    result = subprocess.run(["docker", "info"], capture_output=True, timeout=10)
    if result.returncode != 0:
        pytest.skip("Docker not available")
```

Tests that previously used `@docker_available` as a decorator switch to accepting `docker_available` as a fixture parameter. Tests that use both `devcontainer_cli` and `docker_available` accept both as parameters. The fixture calls `pytest.skip()` internally, so the test body is never reached if Docker is unavailable.

---

## Section 4: New tests

### `test_cli_entrypoint_runs` (in `test_template.py`)

After `uv sync`, run the actual CLI entry point:
```python
result = subprocess.run(["uv", "run", cli_command, "--help"], cwd=generated, ...)
assert result.returncode == 0
```
This catches regressions in `[project.scripts]`.

### `test_copier_answers_file_exists` (in `test_template.py`)

Assert `.copier-answers.yml` exists in a generated project and is valid YAML.

### `test_copier_update_works` (in `test_template.py`)

Generate a project, then run `copier.run_update` on it with the same template. Assert it completes without error. This validates the update path works — the whole reason copier is used.

### `test_generated_project_tests_pass` parametrized

Currently uses only Python 3.13. Parametrize over `["3.12", "3.13"]`. (3.14 is pre-release; skip.)

### `test_terraform_validate_passes` (in `test_template.py`, marked `@pytest.mark.slow`)

Generate with `use_terraform=True`, then:
```bash
terraform init && terraform validate
```
in the `infra/` directory. Skipped if `terraform` is not in PATH.

---

## Architecture notes

- `tests/_helpers.py` is not a conftest — it does not use pytest's plugin system. Imports are explicit: `from tests._helpers import DEFAULTS, devcontainer_variants`.
- The variant matrix expansion (adding `terraform+aws` and `cuda+dind` combos) means `devcontainer_variants` must add `use_docker_in_docker` as a parameter. All parametrized tests in `test_devcontainer_syntax_when_rendered.py` and `test_devcontainer_build.py` accept this new parameter.
- The CUDA+dind combination test is marked `@pytest.mark.slow` because it pulls CUDA images.
