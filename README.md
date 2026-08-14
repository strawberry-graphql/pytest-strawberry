<img src="https://github.com/strawberry-graphql/strawberry/raw/main/.github/logo.png" width="124" height="150" alt="Strawberry GraphQL logo">

# pytest-strawberry

> Pytest plugin for Strawberry GraphQL

`pytest-strawberry` measures which Strawberry GraphQL schema fields are reached
while your pytest suite runs. It reports schema field coverage independently of
Python source coverage.

## Installation

```shell
pip install pytest-strawberry
```

Pytest loads the plugin automatically through its `pytest11` entry point.

## Field coverage

Enable coverage on the pytest command line:

```shell
pytest --strawberry-coverage
```

By default, the report covers fields with explicit Strawberry resolvers. This
keeps the denominator focused on application behavior rather than data-model
attribute access:

```text
============================= Strawberry coverage =============================
Subscriptions: excluded (requires graphql-core 3.3+); graphql-core 3.2.11

Schema a83c741d
┌───────────┬────────┬──────┬─────────┬────────────────┐
│ Type      │ Fields │ Miss │   Cover │ Missing fields │
├───────────┼────────┼──────┼─────────┼────────────────┤
│ Query     │      2 │    0 │ 100.00% │                │
│ User      │      3 │    1 │  66.67% │ email          │
├───────────┼────────┼──────┼─────────┼────────────────┤
│ All types │      5 │    1 │  80.00% │                │
└───────────┴────────┴──────┴─────────┴────────────────┘

Overall coverage: 80.00% (4/5 fields, 1 missing)
```

Use `all` mode to include Strawberry fields that use default attribute
resolution:

```shell
pytest --strawberry-coverage --strawberry-coverage-mode=all
```

A field counts as covered when GraphQL execution reaches its resolver or
default lookup. A resolver that raises still counts. Fields skipped by a
directive, omitted from the operation, or bypassed by null propagation do not.
Aliases and fragments do not create additional field coordinates.

You can enforce a minimum combined percentage:

```shell
pytest --strawberry-coverage --strawberry-coverage-fail-under=90
```

The threshold is compared with the displayed percentage rounded to two decimal
places. Mode and threshold options require `--strawberry-coverage`.

Structurally different field universes receive separate fingerprinted tables;
identical universes are merged. The final threshold uses their combined field
and hit totals. Coverage from pytest-xdist workers is merged automatically.

### Subscriptions

Subscription resolver extensions are supported by graphql-core 3.3 and newer.
With that capability available, subscription source and payload fields are
included normally. graphql-core 3.2 does not run resolver extensions for
subscriptions, so subscription-only fields are excluded and the plugin emits
one warning if a subscription executes. Query and mutation coverage remains
available in the same run.

Only schemas used to execute an operation during the pytest session are
reported. An observed schema with no eligible fields is 100% covered; a session
that observes no schemas is 0% covered. Reporting and threshold enforcement are
disabled under `--collect-only`.

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
