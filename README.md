# python-copier-template

A [copier](https://copier.readthedocs.io/) template for opinionated Python projects.

## Features

- uv build backend
- ruff (lint + format)
- ty (type checker)
- pytest with coverage
- pre-commit hooks
- GitHub Actions CI (lint, typecheck, test — parallel jobs)
- Optional Terraform CI/CD workflow (fmt, lint, plan, apply)
- devcontainer (VS Code), with optional CUDA/GPU support
- typer CLI entrypoint via uv script
- justfile for common commands
- GitHub Issue templates (bug report, feature request)

## Usage

```bash
uvx copier copy gh:SrzStephen/python-copier-template my-new-project
```

## Questions

| Question          | Description                                    |
| ----------------- | ---------------------------------------------- |
| `project_name`    | Human-readable name                            |
| `package_name`    | Python package name (snake_case, auto-derived) |
| `description`     | One-line description                           |
| `author_name`     | Your name                                      |
| `author_email`    | Your email                                     |
| `github_username` | GitHub username (default: `SrzStephen`)        |
| `python_version`  | `3.12` / `3.13` / `3.14` / `3.12,3.13` / `3.13,3.14` (CI matrix) |
| `cli_command`     | CLI command name (auto-derived)                |
| `use_terraform`   | Include Terraform CI/CD workflow (default: no) |
| `use_cuda`        | CUDA/GPU support in devcontainer (default: no) |
