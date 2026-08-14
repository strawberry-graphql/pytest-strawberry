# AGENTS.md

pytest-strawberry

- Repo: https://github.com/strawberry-graphql/pytest-strawberry

## Setup

```shell
uv sync
uv run pre-commit install
```

## Commands

- Test: `uv run pytest`
- Type check: `uv run mypy`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Check formatting: `uv run ruff format --check .`
- Build: `uv build`
- Run all pre-commit hooks: `uv run pre-commit run --all-files`

## Engineering principles

- Keep the public plugin behavior small, typed, and unsurprising.
- Test installed pytest behavior rather than implementation details.
- Add fixtures, hooks, and options only when they have a concrete use case.
- Keep documentation, tests, and release notes aligned with user-visible
  behavior.

## Pull requests

- Include a `RELEASE.md` for package behavior changes.
- Use `patch`, `minor`, or `major` as the release type.
- Add tests for behavior changes and update the README when public behavior
  changes.
