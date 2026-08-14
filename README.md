<img src="https://github.com/strawberry-graphql/strawberry/raw/main/.github/logo.png" width="124" height="150" alt="Strawberry GraphQL logo">

# pytest-strawberry

> Pytest plugin for Strawberry GraphQL

This repository currently provides the package and release infrastructure for
`pytest-strawberry`. The installed package is discovered automatically by
pytest, but it does not expose fixtures, hooks, or command-line options yet.

## Installation

```shell
pip install pytest-strawberry
```

Pytest loads the plugin automatically through its `pytest11` entry point.

## Development

Install the project and its development dependencies with
[uv](https://docs.astral.sh/uv/):

```shell
uv sync
```

Run the checks with:

```shell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv build
```

## Releases

Release changes are proposed through pull requests containing a `RELEASE.md`.
After the pull request is merged into `main`, AutoPub prepares and publishes the
release.

## Licensing

The code in this project is licensed under the MIT license. See
[LICENSE](./LICENSE) for more information.
