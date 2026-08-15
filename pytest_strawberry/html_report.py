"""Self-contained HTML reporting for Strawberry field coverage."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_strawberry.coverage import (
        CoverageController,
        CoverageReport,
        FieldCoverage,
        SchemaCoverage,
        TypeCoverage,
    )

CoverageTone = Literal["high", "medium", "low"]

_HIGH_COVERAGE = 80
_LOW_COVERAGE = 50
_FULL_COVERAGE = 100

_STYLE = """
:root {
  color-scheme: light dark;
  --canvas: #ffffff;
  --surface: #fafafa;
  --text: #18181b;
  --text-muted: #71717a;
  --border: rgb(24 24 27 / 10%);
  --border-strong: rgb(24 24 27 / 20%);
  --accent: #be123c;
  --high: #15803d;
  --high-soft: #dcfce7;
  --medium: #a16207;
  --low: #b91c1c;
  --low-soft: #fee2e2;
  --excluded: #78716c;
  --excluded-soft: #f5f5ed;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --column-row-height: 1.75rem;
  --cell-x: 0.5rem;
  --type-columns: minmax(0, 1fr) 4.5rem 3rem 3rem;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
  font-synthesis: none;
}

* {
  box-sizing: border-box;
}

html {
  background: var(--canvas);
  -webkit-font-smoothing: antialiased;
}

body {
  min-width: 20rem;
  margin: 0;
  background: var(--canvas);
  color: var(--text);
  font-size: 1rem;
  line-height: 1.5;
}

h1,
h2,
p {
  margin: 0;
}

code {
  font-family: var(--mono);
  font-size: 1em;
}

.page {
  isolation: isolate;
  max-width: 90rem;
  padding: 1.5rem 1rem 2rem;
}

h1 {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.summary {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 0.75rem;
  margin-top: 0.75rem;
}

.summary-score {
  color: var(--tone);
  font-size: 1.75rem;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.summary-detail,
.metadata {
  color: var(--text-muted);
}

.metadata {
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

[data-tone="high"] {
  --tone: var(--high);
}

[data-tone="medium"] {
  --tone: var(--medium);
}

[data-tone="low"] {
  --tone: var(--low);
}

.notices {
  display: grid;
  gap: 0.25rem;
  margin-top: 1rem;
}

.notice strong {
  color: var(--tone);
  font-weight: 600;
}

.notice span {
  color: var(--text-muted);
}

.report-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0 1.5rem;
  margin-top: 1.25rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
}

.report-control {
  display: flex;
  align-items: center;
  min-height: 2.75rem;
  gap: 0.625rem;
  cursor: pointer;
}

.report-control input {
  flex: none;
  width: 1.25rem;
  height: 1.25rem;
  margin: 0;
  accent-color: var(--accent);
}

.report-control input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.report-control:has(input:disabled) {
  color: var(--text-muted);
  cursor: not-allowed;
}

.report-control-count {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.page:has(#hide-fully-covered:checked) .type[data-fully-covered="true"] {
  display: none;
}

.page:not(:has(#show-excluded-fields:checked))
  .field-row[data-status="excluded"],
.page:not(:has(#show-excluded-fields:checked))
  .type[data-only-excluded="true"] {
  display: none;
}

.schemas {
  margin-top: 1.5rem;
}

.schema + .schema {
  margin-top: 2.5rem;
}

.schema-header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 0.75rem;
  padding-bottom: 0.5rem;
}

.schema-identity {
  font-size: 1rem;
  font-weight: 600;
}

.schema-summary {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.schema-summary strong {
  color: var(--tone);
  font-variant-numeric: tabular-nums;
}

.empty-state {
  padding: 1.5rem 0;
  border-top: 1px solid var(--border);
}

.empty-state h2 {
  font-size: 1rem;
  font-weight: 600;
}

.empty-state p {
  max-width: 40rem;
  color: var(--text-muted);
}

.type-columns,
.type-header-row,
.type-total {
  display: grid;
  grid-template-columns: var(--type-columns);
  align-items: baseline;
  column-gap: 0.5rem;
  padding-right: var(--cell-x);
  padding-left: var(--cell-x);
}

.type-columns > :not(:first-child),
.type-header-row > :not(:first-child),
.type-total > :not(:first-child) {
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.type-columns {
  position: sticky;
  top: 0;
  z-index: 2;
  align-items: center;
  height: var(--column-row-height);
  border-top: 1px solid var(--border-strong);
  border-bottom: 1px solid var(--border-strong);
  background: var(--canvas);
  color: var(--text-muted);
  font-size: 0.75rem;
  line-height: 1;
}

.type {
  border-bottom: 1px solid var(--border-strong);
}

.type-header-row {
  position: sticky;
  top: var(--column-row-height);
  z-index: 1;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.type-identity {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  grid-column: 1 / -1;
  min-width: 0;
  gap: 0 0.75rem;
}

.type-name {
  font-family: var(--mono);
  font-weight: 600;
  overflow-wrap: anywhere;
}

.type-location {
  color: var(--text-muted);
  font-family: var(--mono);
  font-size: 0.8125rem;
  overflow-wrap: anywhere;
}

.type-percentage {
  color: var(--tone);
  font-weight: 600;
}

.type-header-row > .type-percentage {
  grid-column: 2;
}

.type-percentage-empty {
  color: var(--text-muted);
  font-weight: 400;
}

.field-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.field-row[data-status="covered"] {
  --field-background: var(--high-soft);
}

.field-row[data-status="missing"] {
  --field-background: var(--low-soft);
}

.field-row[data-status="excluded"] {
  --field-background: var(--excluded-soft);
}

.field-row > * {
  padding: 0.375rem var(--cell-x);
  border-top: 1px solid var(--border);
  background: var(--field-background, transparent);
  font-weight: 400;
  vertical-align: baseline;
}

.field-row:first-child > * {
  border-top: 0;
}

.field-content {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 0.5rem;
}

.field-content > * {
  min-width: 0;
  overflow-wrap: anywhere;
}

.field-row[data-status="excluded"] .field-name-cell {
  color: var(--text-muted);
}

.field-row[data-status="excluded"] .field-status-cell {
  color: var(--excluded);
}

.field-location,
.field-resolution {
  color: var(--text-muted);
  font-family: var(--mono);
  font-size: 0.875rem;
}

.field-location {
  white-space: nowrap;
}

.field-status-cell {
  width: 1%;
  color: var(--text-muted);
  font-size: 0.875rem;
  text-align: right;
  white-space: nowrap;
}

.field-row[data-status="missing"] .field-status-cell {
  color: var(--low);
}

.type-total {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-strong);
  font-weight: 600;
}

.report-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.25rem 1.5rem;
  margin-top: 2rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.8125rem;
}

.report-footer span {
  overflow-wrap: anywhere;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (min-width: 48rem) {
  :root {
    --cell-x: 0.75rem;
    --type-columns: minmax(0, 1fr) 5.5rem 4rem 4rem;
  }

  .page {
    padding: 2.5rem 3rem 3rem;
  }

  h1 {
    font-size: 1.75rem;
  }

  .summary-score {
    font-size: 2rem;
  }

  .report-control {
    min-height: 2.25rem;
    font-size: 0.875rem;
  }

  .report-control input {
    width: 1rem;
    height: 1rem;
  }

  .type-identity {
    grid-column: auto;
  }

  .type-header-row,
  .type-total,
  .field-row > * {
    font-size: 0.875rem;
  }

  .field-row > * {
    padding-top: 0.3125rem;
    padding-bottom: 0.3125rem;
  }

  .field-location,
  .field-resolution,
  .field-status-cell {
    font-size: 0.8125rem;
  }
}

@media (prefers-color-scheme: dark) {
  :root {
    --canvas: #09090b;
    --surface: #18181b;
    --text: #f4f4f5;
    --text-muted: #a1a1aa;
    --border: rgb(244 244 245 / 10%);
    --border-strong: rgb(244 244 245 / 20%);
    --accent: #fb7185;
    --high: #4ade80;
    --high-soft: rgb(74 222 128 / 14%);
    --medium: #fbbf24;
    --low: #f87171;
    --low-soft: rgb(248 113 113 / 14%);
    --excluded: #a8a29e;
    --excluded-soft: rgb(250 204 21 / 9%);
  }
}

@media print {
  :root {
    color-scheme: light;
    --canvas: #ffffff;
    --surface: #fafafa;
    --text: #18181b;
    --text-muted: #52525b;
    --border: rgb(24 24 27 / 15%);
    --border-strong: rgb(24 24 27 / 30%);
    --high-soft: #dcfce7;
    --low-soft: #fee2e2;
    --excluded: #57534e;
    --excluded-soft: #f5f5ed;
  }

  .page {
    max-width: none;
    padding: 0;
  }

  .type-columns,
  .type-header-row {
    position: static;
  }

  .report-controls {
    display: none;
  }

  .type-header-row,
  .field-row,
  .type-total,
  .report-footer {
    break-inside: avoid;
  }
}
"""


def write_html_report(
    output_directory: Path,
    report: CoverageReport,
    controller: CoverageController,
) -> Path:
    """Write a self-contained HTML report and return its entry path."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "index.html"
    report_path.write_text(
        _render_page(report, controller),
        encoding="utf-8",
    )
    return report_path


def _render_page(report: CoverageReport, controller: CoverageController) -> str:
    mode = "All fields" if controller.mode == "all" else "Resolvers only"
    schema_count = len(report.schemas)
    schemas = "\n".join(
        _render_schema(schema, position, labelled=schema_count > 1)
        for position, schema in enumerate(report.schemas, start=1)
    )
    details = (
        f"""
        <section class="schemas" aria-label="Schema coverage">
          {schemas}
        </section>
        """
        if report.schemas
        else """
        <section class="schemas" aria-labelledby="no-schemas">
          <div class="empty-state">
            <h2 id="no-schemas">No schemas observed</h2>
            <p>
              Run at least one GraphQL operation to collect Strawberry field
              coverage.
            </p>
          </div>
        </section>
        """
    )
    notices = _render_notices(report, controller)
    controls = _render_controls(report, controller)
    metadata = [mode, f"graphql-core {escape(controller.graphql_version)}"]
    if controller.subscription_executed():
        metadata.append(
            "subscriptions included"
            if controller.supports_subscriptions
            else "subscriptions excluded"
        )
    metadata.append(f"{schema_count} {_plural(schema_count, 'schema')}")
    tone = _coverage_tone(report.percentage)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light dark">
    <title>Strawberry field coverage</title>
    <style>{_STYLE}</style>
  </head>
  <body>
    <main class="page">
      <header class="report-header">
        <h1>Strawberry coverage</h1>
        <p class="summary">
          <strong class="summary-score" data-tone="{tone}">
            {report.percentage:.2f}%
          </strong>
          <span class="summary-detail">
            {report.hit_count}/{report.field_count} fields covered ·
            {report.missing_count} missing
          </span>
        </p>
        <p class="metadata">{" · ".join(metadata)}</p>
      </header>

      {notices}
      {controls}
      {details}

      <footer class="report-footer">
        <span>Generated by pytest-strawberry</span>
        <span>{mode} · graphql-core {escape(controller.graphql_version)}</span>
      </footer>
    </main>
  </body>
</html>
"""


def _render_notices(
    report: CoverageReport,
    controller: CoverageController,
) -> str:
    notices: list[str] = []
    if controller.fail_under is not None:
        threshold_met = not controller.threshold_failed
        tone: CoverageTone = "high" if threshold_met else "low"
        state = "met" if threshold_met else "not met"
        operator = ">=" if threshold_met else "<"
        notices.append(
            f"""
        <p class="notice" data-tone="{tone}">
          <strong>Coverage threshold {state}.</strong>
          <span>
            {report.percentage:.2f}% {operator} {controller.fail_under:.2f}%.
          </span>
        </p>"""
        )
    if controller.subscription_warning_needed():
        notices.append(
            """
        <p class="notice" data-tone="medium">
          <strong>Subscription coverage is unavailable.</strong>
          <span>
            graphql-core 3.2 does not run resolver extensions for subscriptions.
          </span>
        </p>"""
        )
    if controller.missing_worker_output:
        notices.append(
            """
        <p class="notice" data-tone="medium">
          <strong>Worker coverage is incomplete.</strong>
          <span>
            Coverage data was unavailable from at least one pytest-xdist worker.
          </span>
        </p>"""
        )
    if not notices:
        return ""
    return f"""
      <section class="notices" aria-label="Coverage status">
        {"".join(notices)}
      </section>
"""


def _render_controls(
    report: CoverageReport,
    controller: CoverageController,
) -> str:
    if not report.schemas:
        return ""

    fully_covered_count = sum(
        type_report.field_count > 0 and not type_report.missing
        for schema in report.schemas
        for type_report in schema.types
    )
    excluded_count = sum(
        not field_report.eligible
        for schema in report.schemas
        for type_report in schema.types
        for field_report in type_report.fields
    )
    hide_disabled = " disabled" if fully_covered_count == 0 else ""
    excluded_control = (
        f"""
        <label class="report-control" for="show-excluded-fields">
          <input
            id="show-excluded-fields"
            name="show-excluded-fields"
            type="checkbox"
            aria-describedby="excluded-fields-description"
          >
          <span>
            Show excluded fields
            <span class="report-control-count">({excluded_count})</span>
          </span>
          <span class="sr-only" id="excluded-fields-description">
            Fields resolved by ordinary attribute lookup and not counted in
            resolver coverage.
          </span>
        </label>"""
        if controller.mode == "resolvers" and excluded_count
        else ""
    )
    return f"""
      <section class="report-controls" aria-label="Report filters">
        <label class="report-control" for="hide-fully-covered">
          <input
            id="hide-fully-covered"
            name="hide-fully-covered"
            type="checkbox"
            {hide_disabled.strip()}
          >
          <span>
            Hide fully covered types
            <span class="report-control-count">({fully_covered_count})</span>
          </span>
        </label>
        {excluded_control}
      </section>
"""


def _render_schema(schema: SchemaCoverage, position: int, *, labelled: bool) -> str:
    tone = _coverage_tone(schema.percentage)
    types = "\n".join(
        _render_type(type_report, schema.fingerprint, type_position)
        for type_position, type_report in enumerate(schema.types, start=1)
    )
    heading_id = f"schema-{schema.fingerprint}"
    header = (
        f"""
            <header class="schema-header">
              <h2 class="schema-identity" id="{heading_id}">Schema {position}</h2>
              <p class="schema-summary">
                <strong data-tone="{tone}">{schema.percentage:.2f}%</strong> ·
                {schema.hit_count}/{schema.field_count} covered ·
                {schema.missing_count} missing
              </p>
            </header>"""
        if labelled
        else ""
    )
    labelling = (
        f'aria-labelledby="{heading_id}"'
        if labelled
        else f'aria-label="Schema {position}"'
    )
    return f"""
          <article class="schema" {labelling}>
            {header}
            <div class="type-list">
              <div class="type-columns" aria-hidden="true">
                <span></span>
                <span>Coverage</span>
                <span>Fields</span>
                <span>Miss</span>
              </div>
              {types}
              <div
                class="type-total"
                aria-label="All types, {schema.percentage:.2f}% coverage,
                  {schema.field_count} fields, {schema.missing_count} missing"
              >
                <strong class="type-total-label">All types</strong>
                <strong class="type-percentage" data-tone="{tone}">
                  {schema.percentage:.2f}%
                </strong>
                <span class="type-number">{schema.field_count}</span>
                <span class="type-number">{schema.missing_count}</span>
              </div>
            </div>
          </article>
"""


def _render_type(
    type_report: TypeCoverage,
    schema_fingerprint: str,
    position: int,
) -> str:
    missing = len(type_report.missing)
    tone = _coverage_tone(type_report.percentage)
    source_files = {
        field_report.location.rsplit(":", maxsplit=1)[0]
        for field_report in type_report.fields
        if field_report.location is not None
    }
    source_file = next(iter(source_files)) if len(source_files) == 1 else None
    fields = "\n".join(
        _render_field(field_report, source_file) for field_report in type_report.fields
    )
    type_id = f"schema-{schema_fingerprint}-type-{position}"
    scored = type_report.field_count > 0
    fully_covered = str(scored and type_report.percentage == _FULL_COVERAGE).lower()
    only_excluded = str(
        bool(type_report.fields) and type_report.field_count == 0
    ).lower()
    source = (
        f'<span class="type-location">{escape(source_file)}</span>'
        if source_file is not None
        else ""
    )
    coverage = (
        f"""<strong class="type-percentage" data-tone="{tone}">
                    {type_report.percentage:.2f}%
                  </strong>"""
        if scored
        else '<span class="type-percentage type-percentage-empty">—</span>'
    )
    coverage_label = (
        f"{type_report.percentage:.2f}% coverage" if scored else "not scored"
    )
    return f"""
              <section
                class="type"
                data-fully-covered="{fully_covered}"
                data-only-excluded="{only_excluded}"
                aria-labelledby="{type_id}"
              >
                <header
                  class="type-header-row"
                  id="{type_id}"
                  aria-label="{escape(type_report.name)},
                    {coverage_label},
                    {type_report.field_count} fields, {missing} missing"
                >
                  <span class="type-identity">
                    <span class="type-name">{escape(type_report.name)}</span>
                    {source}
                  </span>
                  {coverage}
                  <span class="type-number">{type_report.field_count}</span>
                  <span class="type-number">{missing}</span>
                </header>
                <table class="field-table">
                  <caption class="sr-only">
                    Field coverage for {escape(type_report.name)}
                  </caption>
                  <tbody>
                    {fields}
                  </tbody>
                </table>
              </section>"""


def _render_field(
    field_report: FieldCoverage,
    source_file: str | None,
) -> str:
    if not field_report.eligible:
        status = "excluded"
    else:
        status = "covered" if field_report.covered else "missing"
    name = escape(field_report.name)
    resolution = " · ".join(escape(item) for item in field_report.resolution)
    details: list[str] = []
    if field_report.location is not None:
        location_file, line_number = field_report.location.rsplit(":", maxsplit=1)
        location = (
            f":{escape(line_number)}"
            if location_file == source_file
            else escape(field_report.location)
        )
        details.append(
            f'<span class="field-location" '
            f'aria-label="{escape(location_file)}, line {escape(line_number)}">'
            f"{location}</span>"
        )
    if resolution:
        details.append(f'<span class="field-resolution">via {resolution}</span>')
    resolution_label = f", via {resolution}" if resolution else ""
    status_label = "not counted" if status == "excluded" else status
    status_text = "" if status == "covered" else status_label
    return f"""
                    <tr
                      class="field-row"
                      data-status="{status}"
                      aria-label="{name}, {status_label}{resolution_label}"
                    >
                      <th class="field-name-cell" scope="row">
                        <span class="field-content">
                          <code>{name}</code>
                          {"".join(details)}
                        </span>
                      </th>
                      <td class="field-status-cell">{status_text}</td>
                    </tr>"""


def _coverage_tone(percentage: float) -> CoverageTone:
    if percentage >= _HIGH_COVERAGE:
        return "high"
    if percentage >= _LOW_COVERAGE:
        return "medium"
    return "low"


def _plural(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"
