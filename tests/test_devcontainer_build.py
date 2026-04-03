"""Tests that the generated devcontainer actually builds via the devcontainer CLI."""

import shutil
import subprocess
from pathlib import Path

import copier
import pytest

from tests.conftest import devcontainer_variants

TEMPLATE_ROOT = Path(__file__).parent.parent

DEFAULTS = {
    "project_name": "My Tool",
    "description": "A handy tool for doing things",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "github_username": "testuser",
    "python_version": "3.13",
}

devcontainer_cli = pytest.mark.skipif(
    shutil.which("devcontainer") is None,
    reason="devcontainer CLI not installed",
)
docker_available = pytest.mark.skipif(
    subprocess.run(["docker", "info"], capture_output=True, timeout=10).returncode != 0
    if shutil.which("docker")
    else True,
    reason="Docker not available",
)


def _build(tmp_path: Path, extra_data: dict) -> subprocess.CompletedProcess:
    copier.run_copy(
        str(TEMPLATE_ROOT),
        tmp_path,
        data={**DEFAULTS, **extra_data},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
    )
    return subprocess.run(
        ["devcontainer", "build", "--workspace-folder", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=900,
    )


@pytest.mark.slow
@devcontainer_cli
@docker_available
@devcontainer_variants
def test_devcontainer_builds(
    tmp_path: Path, use_terraform: bool, use_cuda: bool, use_aws: bool, use_azure: bool
) -> None:
    result = _build(
        tmp_path,
        {
            "use_terraform": use_terraform,
            "use_cuda": use_cuda,
            "use_aws": use_aws,
            "use_azure": use_azure,
        },
    )
    assert result.returncode == 0, (
        f"devcontainer build failed (use_terraform={use_terraform}, use_cuda={use_cuda}, use_aws={use_aws}, use_azure={use_azure}):\n{result.stdout}\n{result.stderr}"
    )
