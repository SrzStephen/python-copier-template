prek:
    uv run prek run --all-files

test *args:
    uv run pytest -m "not slow" {{args}} -rsx

test-slow *args:
    uv run pytest -m slow {{args}} -rsx
