"""Tests to verify the copier template generates correctly."""

import itertools
import subprocess
from pathlib import Path

import copier
import json5
import pytest

TEMPLATE_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = TEMPLATE_ROOT / "template"

DEFAULTS = {
    "project_name": "My Tool",
    "description": "A handy tool for doing things",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "github_username": "testuser",
    "python_version": "3.13",
}


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dst = tmp_path_factory.mktemp("project")
    copier.run_copy(
        str(TEMPLATE_ROOT),
        dst,
        data=DEFAULTS,
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    return dst


def test_expected_files_exist(generated: Path) -> None:
    expected = [
        "pyproject.toml",
        "justfile",
        ".editorconfig",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".devcontainer/devcontainer.json",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        "src/my_tool/__init__.py",
        "src/my_tool/cli.py",
        "src/my_tool/py.typed",
        "tests/__init__.py",
        "tests/test_cli.py",
    ]
    for path in expected:
        assert (generated / path).exists(), f"Missing expected file: {path}"


def test_pyproject_toml_rendered(generated: Path) -> None:
    content = (generated / "pyproject.toml").read_text()
    assert 'name = "my-tool"' in content
    assert 'description = "A handy tool for doing things"' in content
    assert '"Test Author"' in content
    assert '"test@example.com"' in content
    assert 'requires-python = ">=3.13"' in content
    assert 'my-tool = "my_tool.cli:app"' in content


def test_readme_rendered(generated: Path) -> None:
    content = (generated / "README.md").read_text()
    assert "My Tool" in content


def test_cli_rendered(generated: Path) -> None:
    content = (generated / "src/my_tool/cli.py").read_text()
    assert "Hello from My Tool!" in content
    assert "My Tool" in content


def test_ci_workflow_rendered(generated: Path) -> None:
    content = (generated / ".github/workflows/ci.yml").read_text()
    assert "3.13" in content
    # GitHub Actions uses ${{ }} syntax — verify it rendered correctly
    assert "${{ matrix.python-version }}" in content


def test_no_jinja_delimiters_in_any_file(generated: Path) -> None:
    # ci.yml intentionally contains ${{ }} GitHub Actions expressions — skip it
    skip_files = {".copier-answers.yml", "ci.yml", "terraform.yml"}
    for path in generated.rglob("*"):
        if not path.is_file():
            continue
        if path.name in skip_files or path.suffix in {".png", ".jpg", ".ico"}:
            continue
        text = path.read_text(errors="replace")
        assert "{{" not in text, (
            f"Unrendered Jinja delimiter in {path.relative_to(generated)}"
        )
        assert "}}" not in text, (
            f"Unrendered Jinja delimiter in {path.relative_to(generated)}"
        )


def test_generated_project_installs(generated: Path) -> None:
    result = subprocess.run(
        ["uv", "sync"],
        cwd=generated,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"uv sync failed:\n{result.stderr}"


def test_generated_project_tests_pass(generated: Path) -> None:
    result = subprocess.run(
        ["uv", "run", "pytest", "--no-header", "-q"],
        cwd=generated,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"pytest failed:\n{result.stdout}\n{result.stderr}"


@pytest.mark.parametrize(
    "python_version", ["3.12", "3.13", "3.14", "3.12,3.13", "3.13,3.14"]
)
def test_python_version_variants(tmp_path: Path, python_version: str) -> None:
    copier.run_copy(
        str(TEMPLATE_ROOT),
        tmp_path,
        data={**DEFAULTS, "python_version": python_version},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    pyproject = (tmp_path / "pyproject.toml").read_text()
    first_version = python_version.split(",")[0]
    assert f'requires-python = ">={first_version}"' in pyproject

    ci = (tmp_path / ".github/workflows/ci.yml").read_text()
    for ver in python_version.split(","):
        assert ver.strip() in ci


def test_terraform_workflow_absent_by_default(generated: Path) -> None:
    assert not (generated / ".github/workflows/terraform.yml").exists()


# itertools.permutations doesn't allow repeats and I need all 4 combos
@pytest.mark.parametrize(
    "use_cuda,use_terraform", itertools.product([False, True], repeat=2)
)
def test_devcontainer_is_valid_jsonc(
    tmp_path: Path, use_cuda: bool, use_terraform: bool
) -> None:
    copier.run_copy(
        str(TEMPLATE_ROOT),
        tmp_path,
        data={**DEFAULTS, "use_cuda": use_cuda, "use_terraform": use_terraform},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    content = (tmp_path / ".devcontainer/devcontainer.json").read_text()
    json5.loads(content)  # raises if invalid


def test_cuda_absent_by_default(generated: Path) -> None:
    content = (generated / ".devcontainer/devcontainer.json").read_text()
    assert "nvidia-cuda" not in content
    assert "hostRequirements" not in content


@pytest.fixture(scope="module")
def generated_with_cuda(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dst = tmp_path_factory.mktemp("project_cuda")
    copier.run_copy(
        str(TEMPLATE_ROOT),
        dst,
        data={**DEFAULTS, "use_cuda": True},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    return dst


def test_cuda_feature_present(generated_with_cuda: Path) -> None:
    content = (generated_with_cuda / ".devcontainer/devcontainer.json").read_text()
    assert "nvidia-cuda" in content
    assert "installCudnn" in content


def test_cuda_host_requirements_present(generated_with_cuda: Path) -> None:
    content = (generated_with_cuda / ".devcontainer/devcontainer.json").read_text()
    assert "hostRequirements" in content
    assert '"gpu"' in content


@pytest.fixture(scope="module")
def generated_with_terraform(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dst = tmp_path_factory.mktemp("project_tf")
    copier.run_copy(
        str(TEMPLATE_ROOT),
        dst,
        data={**DEFAULTS, "use_terraform": True},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    return dst


def test_terraform_workflow_generated(generated_with_terraform: Path) -> None:
    assert (generated_with_terraform / ".github/workflows/terraform.yml").exists()


def test_terraform_infra_folder_present(generated_with_terraform: Path) -> None:
    expected = [
        "infra/main.tf",
        "infra/outputs.tf",
        "infra/provider.tf",
        "infra/variables.tf",
    ]
    for path in expected:
        assert (generated_with_terraform / path).exists(), f"Missing: {path}"


def test_terraform_infra_folder_absent_by_default(generated: Path) -> None:
    assert not (generated / "infra").exists()


def test_terraform_workflow_content(generated_with_terraform: Path) -> None:
    content = (generated_with_terraform / ".github/workflows/terraform.yml").read_text()
    assert "terraform fmt -check" in content
    assert "tflint" in content
    assert "terraform plan" in content
    assert "terraform test" in content
    assert "terraform apply" in content
    assert "1.14" in content
    assert "working-directory: infra" in content
    # apply only on main
    assert "github.ref == 'refs/heads/main'" in content
    # GitHub Actions ${{ }} syntax rendered correctly
    assert "${{ github.ref }}" in content
