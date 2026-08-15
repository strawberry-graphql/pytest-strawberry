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

_STYLE = """
:root {
  color-scheme: light dark;
  --canvas: #ffffff;
  --surface: #fafafa;
  --surface-strong: #f4f4f5;
  --text: #18181b;
  --text-muted: #71717a;
  --border: rgb(24 24 27 / 10%);
  --border-strong: rgb(24 24 27 / 18%);
  --accent: #be123c;
  --accent-soft: #fff1f2;
  --high: #15803d;
  --high-soft: #f0fdf4;
  --medium: #a16207;
  --medium-soft: #fffbeb;
  --low: #b91c1c;
  --low-soft: #fef2f2;
  --radius: 1rem;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
  font-feature-settings: "cv02", "cv03", "cv04", "cv11";
  font-synthesis: none;
}

* {
  box-sizing: border-box;
}

html {
  background: var(--canvas);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

body {
  min-width: 20rem;
  margin: 0;
  background: var(--canvas);
  color: var(--text);
}

.page {
  isolation: isolate;
  width: 100%;
  max-width: 90rem;
  padding: 1.5rem 1rem;
}

.report-header {
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
}

h1,
h2,
h3,
h4,
p {
  margin-top: 0;
}

h1,
h2,
h3,
h4 {
  color: var(--text);
  font-weight: 600;
  text-wrap: balance;
}

h1 {
  margin-bottom: 0.375rem;
  font-size: 1.5rem;
  letter-spacing: -0.035em;
}

h2 {
  margin-bottom: 0.375rem;
  font-size: clamp(1.375rem, 4vw, 1.625rem);
  letter-spacing: -0.025em;
}

h3 {
  margin-bottom: 0;
  font-size: 1.125rem;
}

.empty-state p {
  color: var(--text-muted);
  font-size: 1rem;
  line-height: 1.5;
  text-wrap: pretty;
}

.metadata {
  margin-bottom: 0;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-style: italic;
  line-height: 1.5;
}

[data-tone="high"] {
  --tone: var(--high);
  --tone-soft: var(--high-soft);
}

[data-tone="medium"] {
  --tone: var(--medium);
  --tone-soft: var(--medium-soft);
}

[data-tone="low"] {
  --tone: var(--low);
  --tone-soft: var(--low-soft);
}

.notices {
  display: grid;
  gap: 0.75rem;
  padding-top: 1.25rem;
}

.notice {
  padding: 0.75rem 0.875rem;
  border-left: 3px solid var(--tone);
  border-radius: 0 var(--radius) var(--radius) 0;
  background: var(--tone-soft);
}

.notice strong,
.notice span {
  font-size: 0.9375rem;
  line-height: 1.5;
}

.notice strong {
  color: var(--tone);
  font-weight: 600;
}

.notice span {
  color: var(--text-muted);
}

.schemas {
  padding-top: 1.75rem;
}

.schema {
  padding-bottom: 2rem;
}

.schema-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.75rem;
}

.schema-identity {
  margin-bottom: 0.25rem;
  font-size: 1.125rem;
}

.schema-score {
  color: var(--tone);
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.schema-count {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 400;
}

.type-list {
  --type-columns: minmax(0, 1fr) 4.75rem 3.25rem 3.25rem;
  border-top: 1px solid var(--border-strong);
}

.type-columns,
.type-header-row,
.type-total {
  display: grid;
  grid-template-columns: var(--type-columns);
  align-items: baseline;
}

.type-columns {
  padding: 0.5rem 0.5rem 0.375rem 0.75rem;
  border-bottom: 1px solid var(--border-strong);
  color: var(--text-muted);
  font-size: 0.75rem;
  font-style: italic;
  font-weight: 500;
}

.type-columns > :not(:first-child),
.type-header-row > :not(:first-child),
.type-total > :not(:first-child) {
  text-align: right;
}

.type {
  border-bottom: 1px solid var(--border);
}

.type-header-row {
  padding: 0.625rem 0.5rem 0.625rem 0.75rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  font-size: 1rem;
}

.type-name {
  min-width: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.type-percentage {
  color: var(--tone);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.type-number {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.field-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  text-align: left;
}

.field-row {
  --field-background: var(--high-soft);
}

.field-row[data-status="missing"] {
  --field-background: var(--low-soft);
}

.field-row > * {
  padding: 0.4375rem 0.75rem;
  border-top: 1px solid var(--border);
  background: var(--field-background);
  font-size: 1rem;
  line-height: 1.5;
}

.field-row:first-child > * {
  border-top: 0;
}

.field-name-cell {
  color: var(--text);
  font-weight: 400;
  overflow-wrap: anywhere;
}

.field-content {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  min-width: 0;
}

.field-resolution {
  min-width: 0;
  color: var(--text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9375rem;
  font-weight: 400;
  overflow-wrap: anywhere;
}

.field-name-cell code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.type-total {
  padding: 0.625rem 0.5rem 0.625rem 0.75rem;
  border-bottom: 1px solid var(--border-strong);
  font-size: 1rem;
  font-weight: 600;
}

.type-total-label {
  color: var(--text);
}

.empty-state {
  padding: 2rem;
  border-radius: var(--radius);
  background: var(--surface);
}

.empty-state h2 {
  margin-bottom: 0.5rem;
  font-size: 1.25rem;
}

.empty-state p {
  margin-bottom: 0;
}

.report-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.8125rem;
}

.report-footer span {
  min-width: 0;
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
  .page {
    padding: 2.5rem 3rem 2rem;
  }

  h1 {
    font-size: 2.125rem;
  }

  .empty-state p {
    font-size: 0.9375rem;
  }

  .type-list {
    --type-columns: minmax(0, 1fr) 5.5rem 4rem 4rem;
  }

  .type-header-row,
  .type-total {
    font-size: 0.875rem;
  }

  .field-row > * {
    font-size: 0.875rem;
  }

  .field-resolution {
    font-size: 0.8125rem;
  }
}

@media (prefers-color-scheme: dark) {
  :root {
    --canvas: #09090b;
    --surface: #18181b;
    --surface-strong: #27272a;
    --text: #f4f4f5;
    --text-muted: #a1a1aa;
    --border: rgb(244 244 245 / 10%);
    --border-strong: rgb(244 244 245 / 18%);
    --accent: #fb7185;
    --accent-soft: #09090b;
    --high: #4ade80;
    --high-soft: rgb(74 222 128 / 6%);
    --medium: #fbbf24;
    --medium-soft: #09090b;
    --low: #f87171;
    --low-soft: rgb(248 113 113 / 7%);
  }

  .notice {
    border-top: 1px solid var(--border);
    border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }
}

@media print {
  :root {
    color-scheme: light;
    --canvas: #ffffff;
    --surface: #fafafa;
    --surface-strong: #f4f4f5;
    --text: #18181b;
    --text-muted: #52525b;
    --border: rgb(24 24 27 / 15%);
    --border-strong: rgb(24 24 27 / 25%);
  }

  .page {
    width: 100%;
    padding: 0;
  }

  .schema-header,
  .type-header-row,
  .field-row,
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
    schemas = "\n".join(
        _render_schema(schema, position)
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
    schema_count = len(report.schemas)
    schema_label = _plural(schema_count, "schema")
    metadata = [mode, f"graphql-core {escape(controller.graphql_version)}"]
    if controller.subscription_executed():
        metadata.append(
            "subscriptions included"
            if controller.supports_subscriptions
            else "subscriptions excluded"
        )
    metadata.extend(
        [
            f"{report.hit_count}/{report.field_count} fields covered",
            f"{schema_count} {schema_label}",
        ]
    )
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
        <p class="metadata">{", ".join(metadata)}</p>
      </header>

      {notices}
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
        <div class="notice" data-tone="{tone}">
          <strong>Coverage threshold {state}.</strong>
          <span>
            {report.percentage:.2f}% {operator} {controller.fail_under:.2f}%.
          </span>
        </div>"""
        )
    if controller.subscription_warning_needed():
        notices.append(
            """
        <div class="notice" data-tone="medium">
          <strong>Subscription coverage is unavailable.</strong>
          <span>
            graphql-core 3.2 does not run resolver extensions for subscriptions.
          </span>
        </div>"""
        )
    if controller.missing_worker_output:
        notices.append(
            """
        <div class="notice" data-tone="medium">
          <strong>Worker coverage is incomplete.</strong>
          <span>
            Coverage data was unavailable from at least one pytest-xdist worker.
          </span>
        </div>"""
        )
    if not notices:
        return ""
    return f"""
      <section class="notices" aria-label="Coverage status">
        {"".join(notices)}
      </section>
"""


def _render_schema(schema: SchemaCoverage, position: int) -> str:
    tone = _coverage_tone(schema.percentage)
    types = "\n".join(
        _render_type(type_report, schema.fingerprint, type_position)
        for type_position, type_report in enumerate(schema.types, start=1)
    )
    return f"""
          <article class="schema" aria-labelledby="schema-{schema.fingerprint}">
            <header class="schema-header">
              <div>
                <h2 class="schema-identity" id="schema-{schema.fingerprint}">
                  Schema {position}
                </h2>
                <p class="schema-count">
                  {schema.hit_count}/{schema.field_count} covered ·
                  {schema.missing_count} missing
                </p>
              </div>
              <strong class="schema-score" data-tone="{tone}">
                {schema.percentage:.2f}%
              </strong>
            </header>
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
    fields = "\n".join(
        _render_field(field_report) for field_report in type_report.fields
    )
    type_id = f"schema-{schema_fingerprint}-type-{position}"
    return f"""
              <section class="type" aria-labelledby="{type_id}">
                <header
                  class="type-header-row"
                  id="{type_id}"
                  aria-label="{escape(type_report.name)},
                    {type_report.percentage:.2f}% coverage,
                    {type_report.field_count} fields, {missing} missing"
                >
                  <span class="type-name">{escape(type_report.name)}</span>
                  <strong class="type-percentage" data-tone="{tone}">
                    {type_report.percentage:.2f}%
                  </strong>
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


def _render_field(field_report: FieldCoverage) -> str:
    status = "covered" if field_report.covered else "missing"
    name = escape(field_report.name)
    resolution = " · ".join(escape(item) for item in field_report.resolution)
    field_content = (
        f"""<div class="field-content">
                          <code>{name}</code>
                          <span class="field-resolution">via {resolution}</span>
                        </div>"""
        if resolution
        else f"<code>{name}</code>"
    )
    resolution_label = f", via {resolution}" if resolution else ""
    return f"""
                    <tr
                      class="field-row"
                      data-status="{status}"
                      aria-label="{name}, {status}{resolution_label}"
                    >
                      <th class="field-name-cell" scope="row">
                        {field_content}
                      </th>
                    </tr>"""


def _coverage_tone(percentage: float) -> CoverageTone:
    if percentage >= _HIGH_COVERAGE:
        return "high"
    if percentage >= _LOW_COVERAGE:
        return "medium"
    return "low"


def _plural(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"
