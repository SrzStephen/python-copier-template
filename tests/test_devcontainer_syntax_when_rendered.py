"""Tests that the rendered devcontainer.json has correct syntax and structure."""

import json
from pathlib import Path

import copier
import json5
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


def _render(tmp_path: Path, extra_data: dict | None = None) -> dict:
    copier.run_copy(
        str(TEMPLATE_ROOT),
        tmp_path,
        data={**DEFAULTS, **(extra_data or {})},
        defaults=True,
        overwrite=True,
        quiet=True,
        unsafe=True,
        vcs_ref="HEAD",
    )
    content = (tmp_path / ".devcontainer/devcontainer.json").read_text()
    return json5.loads(content)


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
    required_keys = {
        "image",
        "name",
        "features",
        "customizations",
        "mounts",
        "remoteEnv",
    }
    missing = required_keys - config.keys()
    assert not missing, f"Missing top-level keys: {missing}"


@devcontainer_variants
def test_extensions_is_list_of_strings(
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
    extensions = config["customizations"]["vscode"]["extensions"]
    assert isinstance(extensions, list), "extensions must be a list"
    for ext in extensions:
        assert isinstance(ext, str) and ext, (
            f"extension must be a non-empty string, got {ext!r}"
        )


@devcontainer_variants
def test_no_duplicate_extensions(
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
    extensions = config["customizations"]["vscode"]["extensions"]
    assert len(extensions) == len(set(extensions)), (
        f"Duplicate extensions found: {[e for e in extensions if extensions.count(e) > 1]}"
    )


@devcontainer_variants
def test_features_is_dict_of_dicts(
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
    features = config["features"]
    assert isinstance(features, dict), "features must be a dict"
    for key, val in features.items():
        assert isinstance(key, str) and key, (
            f"feature key must be a non-empty string, got {key!r}"
        )
        assert isinstance(val, dict), (
            f"feature value for {key!r} must be a dict, got {val!r}"
        )


@devcontainer_variants
def test_mounts_is_list_of_strings(
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
    mounts = config["mounts"]
    assert isinstance(mounts, list), "mounts must be a list"
    for mount in mounts:
        assert isinstance(mount, str) and mount, (
            f"mount must be a non-empty string, got {mount!r}"
        )


@devcontainer_variants
def test_forward_ports_is_list_of_ints(
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
    ports = config.get("forwardPorts", [])
    assert isinstance(ports, list), "forwardPorts must be a list"
    for port in ports:
        assert isinstance(port, int), f"port must be an int, got {port!r}"


def test_terraform_extension_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_terraform": True})
    extensions = config["customizations"]["vscode"]["extensions"]
    assert "hashicorp.terraform" in extensions


def test_terraform_extension_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_terraform": False})
    extensions = config["customizations"]["vscode"]["extensions"]
    assert "hashicorp.terraform" not in extensions


def test_terraform_feature_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_terraform": True})
    feature_keys = list(config["features"].keys())
    assert any("terraform" in k for k in feature_keys), (
        f"No terraform feature found in: {feature_keys}"
    )


def test_terraform_feature_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_terraform": False})
    feature_keys = list(config["features"].keys())
    assert not any("terraform" in k for k in feature_keys), (
        f"Unexpected terraform feature found in: {feature_keys}"
    )


def test_aws_extension_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_aws": True})
    extensions = config["customizations"]["vscode"]["extensions"]
    assert "amazonwebservices.aws-toolkit-vscode" in extensions


def test_aws_extension_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_aws": False})
    extensions = config["customizations"]["vscode"]["extensions"]
    assert "amazonwebservices.aws-toolkit-vscode" not in extensions


def test_aws_feature_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_aws": True})
    feature_keys = list(config["features"].keys())
    assert any("aws-cli" in k for k in feature_keys), (
        f"No aws-cli feature found in: {feature_keys}"
    )


def test_aws_feature_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_aws": False})
    feature_keys = list(config["features"].keys())
    assert not any("aws-cli" in k for k in feature_keys), (
        f"Unexpected aws-cli feature found in: {feature_keys}"
    )


def test_azure_extension_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_azure": True})
    extensions = config["customizations"]["vscode"]["extensions"]
    assert "ms-vscode.vscode-node-azure-pack" in extensions


def test_azure_extension_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_azure": False})
    extensions = config["customizations"]["vscode"]["extensions"]
    assert "ms-vscode.vscode-node-azure-pack" not in extensions


def test_azure_feature_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_azure": True})
    feature_keys = list(config["features"].keys())
    assert any("azure-cli" in k for k in feature_keys), (
        f"No azure-cli feature found in: {feature_keys}"
    )


def test_azure_feature_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_azure": False})
    feature_keys = list(config["features"].keys())
    assert not any("azure-cli" in k for k in feature_keys), (
        f"Unexpected azure-cli feature found in: {feature_keys}"
    )


@pytest.mark.slow
def test_cuda_feature_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_cuda": True})
    feature_keys = list(config["features"].keys())
    assert any("nvidia-cuda" in k for k in feature_keys), (
        f"No nvidia-cuda feature found in: {feature_keys}"
    )


def test_cuda_feature_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_cuda": False})
    feature_keys = list(config["features"].keys())
    assert not any("nvidia-cuda" in k for k in feature_keys), (
        f"Unexpected nvidia-cuda feature found in: {feature_keys}"
    )


def test_docker_in_docker_feature_present_when_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_docker_in_docker": True})
    feature_keys = list(config["features"].keys())
    assert any("docker-in-docker" in k for k in feature_keys), (
        f"No docker-in-docker feature found in: {feature_keys}"
    )


def test_docker_in_docker_feature_absent_when_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_docker_in_docker": False})
    feature_keys = list(config["features"].keys())
    assert not any("docker-in-docker" in k for k in feature_keys), (
        f"Unexpected docker-in-docker feature found in: {feature_keys}"
    )


@pytest.mark.slow
def test_nvidia_container_toolkit_present_when_docker_and_cuda(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_docker_in_docker": True, "use_cuda": True})
    feature_keys = list(config["features"].keys())
    assert any("nvidia-container-toolkit" in k for k in feature_keys), (
        f"No nvidia-container-toolkit feature found in: {feature_keys}"
    )


def test_nvidia_container_toolkit_absent_without_docker(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_docker_in_docker": False, "use_cuda": True})
    feature_keys = list(config["features"].keys())
    assert not any("nvidia-container-toolkit" in k for k in feature_keys), (
        f"Unexpected nvidia-container-toolkit feature found in: {feature_keys}"
    )


def test_run_args_gpus_present_when_cuda_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_cuda": True})
    assert config.get("runArgs") == ["--gpus=all"], (
        "Expected runArgs=['--gpus=all'] when use_cuda=True"
    )


def test_run_args_absent_when_cuda_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_cuda": False})
    assert "runArgs" not in config, "Unexpected runArgs when use_cuda=False"


def test_host_requirements_gpu_present_when_cuda_enabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_cuda": True})
    assert config.get("hostRequirements", {}).get("gpu") == "optional", (
        "Expected hostRequirements.gpu='optional' when use_cuda=True"
    )


def test_host_requirements_absent_when_cuda_disabled(tmp_path: Path) -> None:
    config = _render(tmp_path, {"use_cuda": False})
    assert "hostRequirements" not in config, (
        "Unexpected hostRequirements when use_cuda=False"
    )


def test_terraform_formatter_setting_present_when_enabled(tmp_path: Path) -> None:
    _render(tmp_path, {"use_terraform": True})
    settings = json.loads((tmp_path / ".vscode/settings.json").read_text())
    assert "[terraform]" in settings, (
        "Expected [terraform] formatter setting when use_terraform=True"
    )


def test_terraform_formatter_setting_absent_when_disabled(tmp_path: Path) -> None:
    _render(tmp_path, {"use_terraform": False})
    settings = json.loads((tmp_path / ".vscode/settings.json").read_text())
    assert "[terraform]" not in settings, (
        "Unexpected [terraform] formatter setting when use_terraform=False"
    )


@devcontainer_variants
def test_vscode_settings_has_required_keys(
    tmp_path: Path, use_terraform: bool, use_cuda: bool, use_aws: bool, use_azure: bool
) -> None:
    _render(
        tmp_path,
        {
            "use_terraform": use_terraform,
            "use_cuda": use_cuda,
            "use_aws": use_aws,
            "use_azure": use_azure,
        },
    )
    devcontainer_settings = json5.loads(
        (tmp_path / ".devcontainer/devcontainer.json").read_text()
    )["customizations"]["vscode"]["settings"]
    vscode_settings = json.loads((tmp_path / ".vscode/settings.json").read_text())
    assert "python.defaultInterpreterPath" in devcontainer_settings, (
        "Missing devcontainer vscode setting: python.defaultInterpreterPath"
    )
    required = {"python.testing.pytestEnabled", "editor.formatOnSave"}
    missing = required - vscode_settings.keys()
    assert not missing, f"Missing vscode settings keys: {missing}"
