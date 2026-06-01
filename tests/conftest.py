import shutil
import subprocess

import pytest

_nvidia_available = bool(shutil.which("nvidia-smi")) and (
    subprocess.run(["nvidia-smi"], capture_output=True).returncode == 0
)
_nvidia_skip = pytest.mark.skipif(
    not _nvidia_available, reason="NVIDIA GPU not available"
)

devcontainer_variants = pytest.mark.parametrize(
    "use_terraform,use_cuda,use_aws,use_azure",
    [
        pytest.param(False, False, False, False, id="base"),
        pytest.param(True, False, False, False, id="terraform"),
        pytest.param(
            False, True, False, False, id="cuda", marks=[pytest.mark.slow, _nvidia_skip]
        ),
        pytest.param(False, False, True, False, id="aws"),
        pytest.param(False, False, False, True, id="azure"),
    ],
)
