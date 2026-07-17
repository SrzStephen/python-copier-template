# python-copier-template

A [copier](https://copier.readthedocs.io/) template for opinionated Python projects.

The intention for this is a **starting point** for new python projects that I create.

## Features

- uv build backend
- ruff (lint + format)
- pyrefly (type checker)
- pytest with coverage
- pre-commit hooks
- GitHub Actions CI (lint, typecheck, test — parallel jobs)
- Optional Terraform CI/CD workflow (fmt, lint, plan, apply)
- devcontainer (VS Code), with optional CUDA/GPU, AWS CLI, or Azure CLI support
- devcontainer caches uv, apt, HuggingFace, and Claude Code auth/project history — host directories are created with the correct user permissions via `initializeCommand` (prevents root-owned directories on Linux with rootful Docker)
- typer CLI entrypoint via uv script
- justfile for common commands
- GitHub Issue templates (bug report, feature request)

## Usage

```bash
uvx copier copy gh:SrzStephen/python-copier-template my-new-project
```

## Deployed file structure

A few files get added based on

```zsh
➜  my-new-project tree -a
.
my-new-project
├── .devcontainer
│   ├── devcontainer.json
│   ├── post-create.sh
│   └── post-start.sh
├── .editorconfig
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── workflows
│       ├── ci.yml
│       └── terraform.yml
├── .gitignore
├── infra
│   ├── main.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── variables.tf
├── variables.tf
├── justfile
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
├── src
│   └── mytool
│       ├── cli.py
│       ├── __init__.py
│       └── py.typed
└── tests
    ├── __init__.py
    └── test_cli.py

```

## Questions

| Question          | Description                                                      |
| ----------------- | ---------------------------------------------------------------- |
| `project_name`    | Human-readable name                                              |
| `package_name`    | Python package name (snake_case, auto-derived)                   |
| `description`     | One-line description                                             |
| `author_name`     | Your name                                                        |
| `author_email`    | Your email                                                       |
| `github_username` | GitHub username (default: `SrzStephen`)                          |
| `python_version`  | `3.12` / `3.13` / `3.14` / `3.12,3.13` / `3.13,3.14` (CI matrix) |
| `cli_command`     | CLI command name (auto-derived)                                  |
| `use_terraform`   | Include Terraform CI/CD workflow (default: no)                   |
| `use_cuda`        | CUDA/GPU support in devcontainer (default: no)                   |
| `use_aws`         | AWS CLI and AWS Toolkit extension in devcontainer (default: no)  |
| `use_azure`       | Azure CLI and Azure extension in devcontainer (default: no)      |
