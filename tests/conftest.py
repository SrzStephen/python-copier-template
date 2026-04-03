import pytest

devcontainer_variants = pytest.mark.parametrize(
    "use_terraform,use_cuda,use_aws,use_azure",
    [
        pytest.param(False, False, False, False, id="base"),
        pytest.param(True, False, False, False, id="terraform"),
        pytest.param(False, True, False, False, id="cuda", marks=pytest.mark.slow),
        pytest.param(False, False, True, False, id="aws"),
        pytest.param(False, False, False, True, id="azure"),
    ],
)
