"""Compatibility test sessions."""

from __future__ import annotations

import nox

nox.needs_version = ">=2026.8.10"
nox.options.default_venv_backend = "uv"

PYTHON = "3.14"
PYTEST_XDIST = "pytest-xdist>=3.6.0,<4.0.0"


@nox.session(python=PYTHON, tags=["compatibility"])
def strawberry_min(session: nox.Session) -> None:
    """Test the lowest supported Strawberry and graphql-core versions."""
    session.install(
        ".",
        PYTEST_XDIST,
        "strawberry-graphql==0.316.0",
        "graphql-core==3.2.11",
    )
    session.run("pytest", "-vv")


@nox.session(python=PYTHON, tags=["compatibility"])
def graphql_core_33(session: nox.Session) -> None:
    """Test subscription coverage with graphql-core 3.3."""
    session.install(".", PYTEST_XDIST, "graphql-core>=3.3.0rc0,<3.4")
    session.run("pytest", "-vv")


@nox.session(python=PYTHON, tags=["compatibility"])
def strawberry_django(session: nox.Session) -> None:
    """Test Strawberry Django support and its runnable example."""
    session.install(".", PYTEST_XDIST, "strawberry-graphql-django==0.87.0")
    session.run("pytest", "-vv")
    session.run(
        "pytest",
        "examples/strawberry_django",
        "-q",
        "--strawberry-coverage",
    )
