test *args:
    uv run pytest -m "not slow" {{args}}

test-slow *args:
    uv run pytest -m slow {{args}}
