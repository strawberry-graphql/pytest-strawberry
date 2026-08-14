# Strawberry Django example

This example uses an unsaved Django model instance, so it needs no database
migrations or external services. Run its dedicated compatibility session from
the repository root with:

```shell
uv run nox -s strawberry_django
```

The session runs the plugin's test suite with Strawberry Django installed, then
runs this example with coverage enabled.

The report includes the generated Django model fields:

```text
Schema b7dc8af0
┌─────────────┬────────┬──────┬─────────┬────────────────┐
│ Python type │ Fields │ Miss │   Cover │ Missing fields │
├─────────────┼────────┼──────┼─────────┼────────────────┤
│ FruitType   │      2 │    1 │  50.00% │ description    │
│ Query       │      1 │    0 │ 100.00% │                │
├─────────────┼────────┼──────┼─────────┼────────────────┤
│ All types   │      3 │    1 │  66.67% │                │
└─────────────┴────────┴──────┴─────────┴────────────────┘

Overall coverage: 66.67% (2/3 fields, 1 missing)
```

Resolver mode includes `FruitType.name` and `FruitType.description` because
`StrawberryDjangoField` supplies custom field resolution. The query covers
`name`, leaving `description` visible in the missing-fields column.

Add `--strawberry-coverage-mode=all` to include ordinary Strawberry attribute
lookups too.
