---
release type: minor
---

This release adds the initial `pytest-strawberry` package.

The package registers itself with pytest through the `pytest11` entry point and
includes the project automation needed to test and publish future plugin
features. It does not expose fixtures, hooks, or command-line options yet.
