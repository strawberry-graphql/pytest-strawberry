"""Pytest plugin for Strawberry GraphQL."""

from __future__ import annotations

from argparse import ArgumentTypeError
from dataclasses import dataclass
from math import isfinite
from shutil import get_terminal_size
from textwrap import wrap
from typing import TYPE_CHECKING, Protocol, cast

import pytest

from pytest_strawberry.coverage import (
    CoverageController,
    CoverageMode,
    CoverageSnapshot,
    SchemaCoverage,
)

if TYPE_CHECKING:
    from collections.abc import Generator

_WORKER_OUTPUT_KEY = "pytest_strawberry_coverage"
_MAX_PERCENTAGE = 100
_HIGH_COVERAGE = 80
_LOW_COVERAGE = 50
_MIN_TABLE_WIDTH = 72
_MAX_TABLE_WIDTH = 160
_SUMMARY_ROW_NAME = "All types"
_TYPE_HEADER = "Python type"


@dataclass
class _PluginState:
    controller: CoverageController | None = None


@dataclass(frozen=True)
class _CoverageRow:
    name: str
    field_count: int
    missing_count: int
    percentage: float
    missing_fields: tuple[str, ...]
    bold: bool = False


_state = _PluginState()


class _WorkerConfig(Protocol):
    workeroutput: dict[str, object]


class _WorkerNode(Protocol):
    workeroutput: dict[str, object]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register Strawberry coverage command-line options."""
    group = parser.getgroup("strawberry", "Strawberry GraphQL")
    group.addoption(
        "--strawberry-coverage",
        action="store_true",
        default=False,
        help="Measure runtime Strawberry GraphQL field coverage.",
    )
    group.addoption(
        "--strawberry-coverage-mode",
        choices=("resolvers", "all"),
        default=None,
        help="Fields to measure: resolver-backed (default) or all fields.",
    )
    group.addoption(
        "--strawberry-coverage-fail-under",
        type=_coverage_percentage,
        default=None,
        metavar="PERCENT",
        help="Fail when Strawberry field coverage is below this percentage.",
    )


def pytest_load_initial_conftests(early_config: pytest.Config) -> None:
    """Install instrumentation before user conftests import their schemas."""
    _configure_coverage(early_config)


def pytest_configure(config: pytest.Config) -> None:
    """Install instrumentation when pytest skips the early-config hook."""
    _configure_coverage(config)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtestloop(session: pytest.Session) -> Generator[None, None, None]:
    """Apply the coverage threshold after xdist workers have returned."""
    yield
    controller = _state.controller
    if (
        controller is None
        or _is_worker(session.config)
        or session.config.getoption("collectonly")
        or controller.fail_under is None
    ):
        return

    controller.threshold_failed = controller.report().percentage < controller.fail_under
    if controller.threshold_failed and session.testsfailed == 0:
        session.testsfailed += 1


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Send a worker's aggregate to the xdist controller."""
    controller = _state.controller
    if controller is None or not _is_worker(session.config):
        return
    worker_config = cast("_WorkerConfig", session.config)
    worker_config.workeroutput[_WORKER_OUTPUT_KEY] = controller.snapshot()


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node: object) -> None:
    """Merge coverage from an optional pytest-xdist worker."""
    controller = _state.controller
    if controller is None:
        return
    worker_node = cast("_WorkerNode", node)
    snapshot = worker_node.workeroutput.get(_WORKER_OUTPUT_KEY)
    if snapshot is None:
        controller.mark_missing_worker_output()
        return
    controller.merge(cast("CoverageSnapshot", snapshot))


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    config: pytest.Config,
) -> None:
    """Render the Strawberry field coverage report."""
    controller = _state.controller
    if controller is None or _is_worker(config) or config.getoption("collectonly"):
        return

    report = controller.report()
    terminalreporter.section("Strawberry coverage", sep="=")
    subscription_status = (
        "included"
        if controller.supports_subscriptions
        else "excluded (requires graphql-core 3.3+)"
    )
    terminalreporter.write_line(
        f"Subscriptions: {subscription_status}; graphql-core "
        f"{controller.graphql_version}"
    )

    if not report.schemas:
        terminalreporter.write_line("No Strawberry schemas were observed.")
    for schema in report.schemas:
        _write_schema_report(terminalreporter, schema)

    terminalreporter.write_line("")
    terminalreporter.write("Overall coverage: ", bold=True)
    _write_percentage(terminalreporter, report.percentage)
    terminalreporter.write_line(
        f" ({report.hit_count}/{report.field_count} fields, "
        f"{report.missing_count} missing)"
    )

    if controller.subscription_warning_needed():
        terminalreporter.write_line(
            "WARNING: Subscription executions did not contribute to Strawberry "
            "coverage because graphql-core 3.2 does not run resolver extensions "
            "for subscriptions.",
            yellow=True,
        )
    if controller.missing_worker_output:
        terminalreporter.write_line(
            "WARNING: Strawberry coverage data was unavailable from at least one "
            "xdist worker.",
            yellow=True,
        )
    if controller.fail_under is not None:
        terminalreporter.write("Coverage threshold: ", bold=True)
        if controller.threshold_failed:
            terminalreporter.write("not met", red=True)
            operator = "<"
        else:
            terminalreporter.write("met", green=True)
            operator = ">="
        terminalreporter.write_line(
            f" ({report.percentage:.2f}% {operator} {controller.fail_under:.2f}%)"
        )


def pytest_unconfigure() -> None:
    """Remove process-global Strawberry instrumentation."""
    if _state.controller is not None:
        _state.controller.uninstall()
        _state.controller = None


def _configure_coverage(config: pytest.Config) -> None:
    enabled = cast("bool", config.getoption("strawberry_coverage"))
    mode = cast("CoverageMode | None", config.getoption("strawberry_coverage_mode"))
    fail_under = cast(
        "float | None", config.getoption("strawberry_coverage_fail_under")
    )
    if not enabled:
        if mode is not None or fail_under is not None:
            msg = (
                "--strawberry-coverage-mode and "
                "--strawberry-coverage-fail-under require --strawberry-coverage"
            )
            raise pytest.UsageError(msg)
        return
    if _state.controller is None:
        _state.controller = CoverageController(mode or "resolvers", fail_under)
        _state.controller.install()


def _coverage_percentage(value: str) -> float:
    try:
        percentage = float(value)
    except ValueError as error:
        msg = "must be a number between 0 and 100"
        raise ArgumentTypeError(msg) from error
    if not isfinite(percentage) or not 0 <= percentage <= _MAX_PERCENTAGE:
        msg = "must be a number between 0 and 100"
        raise ArgumentTypeError(msg)
    return percentage


def _is_worker(config: pytest.Config) -> bool:
    return hasattr(config, "workerinput")


def _write_schema_report(
    terminalreporter: pytest.TerminalReporter, schema: SchemaCoverage
) -> None:
    terminalreporter.write_line("")
    terminalreporter.write_line(f"Schema {schema.fingerprint}", bold=True)

    type_width = max(
        len(_TYPE_HEADER),
        len(_SUMMARY_ROW_NAME),
        *(len(type_report.name) for type_report in schema.types),
    )
    fields_width = len("Fields")
    missing_count_width = len("Miss")
    coverage_width = len("100.00%")
    fixed_width = type_width + fields_width + missing_count_width + coverage_width + 16
    terminal_width = min(
        max(get_terminal_size(fallback=(120, 24)).columns, _MIN_TABLE_WIDTH),
        _MAX_TABLE_WIDTH,
    )
    available_missing_fields_width = max(12, terminal_width - fixed_width)
    desired_missing_fields_width = max(
        len("Missing fields"),
        max(
            (len(", ".join(type_report.missing)) for type_report in schema.types),
            default=0,
        ),
    )
    missing_fields_width = min(
        desired_missing_fields_width,
        available_missing_fields_width,
    )
    widths = (
        type_width,
        fields_width,
        missing_count_width,
        coverage_width,
        missing_fields_width,
    )

    terminalreporter.write_line(_table_border("┌", "┬", "┐", widths))
    terminalreporter.write_line(
        _table_row(
            (_TYPE_HEADER, "Fields", "Miss", "Cover", "Missing fields"),
            widths,
            align_right=(False, True, True, True, False),
        ),
        bold=True,
    )
    terminalreporter.write_line(_table_border("├", "┼", "┤", widths))
    for type_report in schema.types:
        _write_coverage_row(
            terminalreporter,
            _CoverageRow(
                name=type_report.name,
                field_count=len(type_report.fields),
                missing_count=len(type_report.missing),
                percentage=type_report.percentage,
                missing_fields=type_report.missing,
            ),
            widths=widths,
        )
    terminalreporter.write_line(_table_border("├", "┼", "┤", widths))
    _write_coverage_row(
        terminalreporter,
        _CoverageRow(
            name=_SUMMARY_ROW_NAME,
            field_count=schema.field_count,
            missing_count=schema.missing_count,
            percentage=schema.percentage,
            missing_fields=(),
            bold=True,
        ),
        widths=widths,
    )
    terminalreporter.write_line(_table_border("└", "┴", "┘", widths))


def _write_coverage_row(
    terminalreporter: pytest.TerminalReporter,
    row: _CoverageRow,
    *,
    widths: tuple[int, ...],
) -> None:
    missing_lines = wrap(
        ", ".join(row.missing_fields),
        width=widths[-1],
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]
    prefix = _table_row_prefix(
        (row.name, str(row.field_count), str(row.missing_count)),
        widths[:3],
    )
    percentage_text = f"{row.percentage:.2f}%".rjust(widths[3])
    terminalreporter.write(prefix, bold=row.bold)
    _write_percentage(
        terminalreporter,
        row.percentage,
        text=percentage_text,
        bold=row.bold,
    )
    terminalreporter.write_line(
        f" │ {missing_lines[0]:<{widths[4]}} │",
        bold=row.bold,
    )

    for missing_line in missing_lines[1:]:
        terminalreporter.write_line(
            _table_row(
                ("", "", "", "", missing_line),
                widths,
                align_right=(False, True, True, True, False),
            )
        )


def _write_percentage(
    terminalreporter: pytest.TerminalReporter,
    percentage: float,
    *,
    text: str | None = None,
    bold: bool = False,
) -> None:
    value = text or f"{percentage:.2f}%"
    if percentage >= _HIGH_COVERAGE:
        terminalreporter.write(value, green=True, bold=bold)
    elif percentage >= _LOW_COVERAGE:
        terminalreporter.write(value, yellow=True, bold=bold)
    else:
        terminalreporter.write(value, red=True, bold=bold)


def _table_border(
    left: str,
    separator: str,
    right: str,
    widths: tuple[int, ...],
) -> str:
    return left + separator.join("─" * (width + 2) for width in widths) + right


def _table_row(
    cells: tuple[str, ...],
    widths: tuple[int, ...],
    *,
    align_right: tuple[bool, ...],
) -> str:
    formatted = (
        f"{cell:>{width}}" if right_aligned else f"{cell:<{width}}"
        for cell, width, right_aligned in zip(cells, widths, align_right, strict=True)
    )
    return "│ " + " │ ".join(formatted) + " │"


def _table_row_prefix(cells: tuple[str, ...], widths: tuple[int, ...]) -> str:
    name, field_count, missing_count = cells
    type_width, fields_width, missing_width = widths
    return (
        f"│ {name:<{type_width}} │ {field_count:>{fields_width}} │ "
        f"{missing_count:>{missing_width}} │ "
    )
