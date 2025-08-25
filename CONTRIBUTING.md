# Contributing

Please follow these steps to set up a productive development environment for this repository.

## Pre-commit hooks (recommended)

We use `pre-commit` to run linters and auto-fixers locally before commits. This helps keep the codebase clean and prevents simple style issues from reaching CI.

Install and enable the hooks:

```bash
pip install pre-commit
pre-commit install
```

To run the hooks against all files (useful for CI or one-off checks):

```bash
pre-commit run --all-files
```

The repository includes a `.pre-commit-config.yaml` that runs `ruff --fix` so unused imports and simple style fixes are applied automatically.

## Running tests

Activate your project's virtualenv and run:

```bash
pip install -r requirements-dev.txt
pytest
```
