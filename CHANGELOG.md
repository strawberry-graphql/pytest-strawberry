CHANGELOG
=========

0.2.0 - 2026-08-14
------------------

Add runtime Strawberry GraphQL field coverage with resolver-only and all-field
modes, custom field resolver support including Strawberry Django, Python-first
terminal reporting, fail-under enforcement, subscription capability detection,
and pytest-xdist aggregation.

This release was contributed by [@patrick91](https://github.com/patrick91) in [#3](https://github.com/strawberry-graphql/pytest-strawberry/pull/3)

0.1.0 - 2026-08-14
------------------

This release adds the initial `pytest-strawberry` package.

The package registers itself with pytest through the `pytest11` entry point and
includes the project automation needed to test and publish future plugin
features. It does not expose fixtures, hooks, or command-line options yet.

This release was contributed by [@patrick91](https://github.com/patrick91) in [#2](https://github.com/strawberry-graphql/pytest-strawberry/pull/2)