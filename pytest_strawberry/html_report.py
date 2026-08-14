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
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
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
  max-width: 68rem;
  margin-inline: auto;
  padding: 1.5rem 1rem;
}

.report-header {
  display: grid;
  gap: 1.5rem;
  padding-bottom: 1.75rem;
  border-bottom: 1px solid var(--border);
}

.title-group {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 0.5rem;
  color: var(--accent);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
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
  max-width: 24ch;
  margin-bottom: 0.5rem;
  font-size: clamp(2rem, 6vw, 3rem);
  letter-spacing: -0.04em;
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

.lede,
.section-description,
.empty-state p {
  color: var(--text-muted);
  font-size: 1rem;
  line-height: 1.5;
  text-wrap: pretty;
}

.lede {
  max-width: 52ch;
  margin-bottom: 0.875rem;
}

.metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.875rem;
}

.metadata-item {
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
}

.score {
  align-self: end;
  min-width: 0;
}

.score-label {
  margin-bottom: 0.25rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 500;
}

.score-value {
  display: block;
  margin-bottom: 0.625rem;
  color: var(--tone);
  font-size: clamp(2.5rem, 9vw, 3.5rem);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  letter-spacing: -0.055em;
}

.meter {
  height: 0.375rem;
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-strong);
}

.meter-fill {
  width: var(--coverage);
  height: 100%;
  border-radius: inherit;
  background: var(--tone);
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

.stats-container {
  container: stats / inline-size;
  padding-block: 1rem;
  border-bottom: 1px solid var(--border);
}

.stats {
  display: grid;
  margin: 0;
}

.stat {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 0.625rem;
}

.stat + .stat {
  border-top: 1px solid var(--border);
}

.stat dt {
  color: var(--text-muted);
  font-size: 1rem;
  font-weight: 500;
  white-space: nowrap;
}

.stat dd {
  margin: 0;
  color: var(--text);
  font-size: 1.375rem;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  letter-spacing: -0.03em;
}

@container stats (min-width: 38rem) {
  .stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .stat {
    display: block;
    min-width: 0;
    padding: 0 1rem;
  }

  .stat:first-child {
    padding-left: 0;
  }

  .stat:last-child {
    padding-right: 0;
  }

  .stat + .stat {
    border-top: 0;
    border-left: 1px solid var(--border);
  }

  .stat dt {
    display: block;
    margin-bottom: 0.25rem;
  }
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
  padding-top: 2.5rem;
}

.section-heading {
  padding-bottom: 1rem;
}

.section-description {
  max-width: 62ch;
  margin-bottom: 0;
}

.schema {
  padding-block: 1.25rem;
  border-top: 1px solid var(--border-strong);
}

.schema-header {
  padding-bottom: 0.875rem;
}

.schema-identity {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  font-size: 0.875rem;
}

.schema-label {
  color: var(--text-muted);
}

.schema-code {
  padding: 0.15rem 0.4rem;
  border-radius: 0.375rem;
  background: var(--surface-strong);
  color: var(--text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 1em;
  font-weight: 500;
}

.schema-score {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.25rem 0.5rem;
  margin-top: 0.75rem;
  color: var(--tone);
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  text-align: left;
}

.schema-count {
  margin: 0;
  color: var(--text-muted);
  font-size: 1rem;
  font-weight: 400;
}

.type-list {
  border-top: 1px solid var(--border);
}

.type {
  padding-block: 1rem;
  border-bottom: 1px solid var(--border);
}

.type-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
}

.type-heading {
  min-width: 0;
}

.type-name {
  margin-bottom: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 1rem;
  overflow-wrap: anywhere;
}

.type-summary {
  margin: 0.375rem 0 0;
  color: var(--text-muted);
  font-size: 1rem;
}

.type-score {
  flex: 0 0 auto;
  color: var(--tone);
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.field-table {
  width: 100%;
  margin-top: 0.625rem;
  border-collapse: collapse;
  table-layout: fixed;
  text-align: left;
}

.field-row {
  --field-tone: var(--high);
}

.field-row[data-status="missing"] {
  --field-tone: var(--low);
}

.field-row > * {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--border);
  font-size: 1rem;
  line-height: 1.5;
}

.field-row:first-child > * {
  border-top: 0;
}

.field-name-cell {
  box-shadow: inset 0.125rem 0 var(--field-tone);
  color: var(--text);
  font-weight: 400;
  overflow-wrap: anywhere;
}

.field-name-cell code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.field-state-cell {
  width: 6.5rem;
  color: var(--field-tone);
  font-weight: 600;
  text-align: right;
  white-space: nowrap;
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
    padding: 2.5rem 1.5rem 2rem;
  }

  .report-header {
    grid-template-columns: minmax(0, 3fr) minmax(15rem, 2fr);
    align-items: end;
    padding-bottom: 2rem;
  }

  .lede,
  .section-description,
  .empty-state p {
    font-size: 0.9375rem;
  }

  .schema-header {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 1.5rem;
  }

  .schema-score {
    flex: 0 0 auto;
    margin-top: 0;
    text-align: right;
  }

  .type-summary {
    font-size: 0.875rem;
  }

  .schema-count {
    font-size: 0.8125rem;
  }

  .field-row > * {
    font-size: 0.875rem;
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

  h1 {
    font-size: 3rem;
  }

  .score-value {
    font-size: 3.5rem;
  }

  .schemas {
    padding-top: 2rem;
  }

  .schema {
    padding-block: 1.25rem;
  }

  .schema-header,
  .type-header,
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
    tone = _coverage_tone(report.percentage)
    mode = "All fields" if controller.mode == "all" else "Resolvers only"
    subscription_status = (
        "Subscriptions included"
        if controller.supports_subscriptions
        else "Subscriptions excluded"
    )
    schemas = "\n".join(
        _render_schema(schema, position)
        for position, schema in enumerate(report.schemas, start=1)
    )
    details = (
        f"""
        <section class="schemas" aria-labelledby="schema-details">
          <div class="section-heading">
            <h2 id="schema-details">Schema details</h2>
            <p class="section-description">
              Every eligible field is grouped under the Python type that defines
              it.
            </p>
          </div>
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
        <div class="title-group">
          <p class="eyebrow">pytest-strawberry</p>
          <h1>Field coverage</h1>
          <p class="lede">
            Runtime coverage of Strawberry GraphQL schema fields.
          </p>
          <div class="metadata" aria-label="Report configuration">
            <span class="metadata-item">{mode}</span>
            <span class="metadata-item">
              graphql-core {escape(controller.graphql_version)}
            </span>
            <span class="metadata-item">{subscription_status}</span>
          </div>
        </div>
        <div class="score" data-tone="{tone}">
          <p class="score-label">Overall coverage</p>
          <strong class="score-value">{report.percentage:.2f}%</strong>
          <div
            class="meter"
            role="progressbar"
            aria-label="Overall field coverage"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow="{report.percentage:.2f}"
          >
            <div
              class="meter-fill"
              style="--coverage: {report.percentage:.2f}%"
            ></div>
          </div>
        </div>
      </header>

      <section class="stats-container" aria-label="Coverage summary">
        <dl class="stats">
          {_render_stat("Covered", report.hit_count, "covered")}
          {_render_stat("Missing", report.missing_count, "missing")}
          {_render_stat("Eligible", report.field_count, "eligible")}
          {_render_stat("Schemas", schema_count, _plural(schema_count, "schema"))}
        </dl>
      </section>

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


def _render_stat(label: str, value: int, spoken_label: str) -> str:
    return f"""
          <div class="stat" aria-label="{value} {spoken_label}">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>"""


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
              <h3 class="schema-identity" id="schema-{schema.fingerprint}">
                <span class="schema-label">Schema {position}</span>
                <code class="schema-code">{schema.fingerprint}</code>
              </h3>
              <div class="schema-score" data-tone="{tone}">
                {schema.percentage:.2f}%
                <p class="schema-count">
                  {schema.hit_count}/{schema.field_count} covered ·
                  {schema.missing_count} missing
                </p>
              </div>
            </header>
            <div class="type-list">
              {types}
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
                <header class="type-header">
                  <div class="type-heading">
                    <h4 class="type-name" id="{type_id}">
                      {escape(type_report.name)}
                    </h4>
                    <p class="type-summary">
                      {type_report.field_count}
                      {_plural(type_report.field_count, "field")} ·
                      {missing} missing
                    </p>
                  </div>
                  <strong class="type-score" data-tone="{tone}">
                    {type_report.percentage:.2f}%
                  </strong>
                </header>
                <table class="field-table">
                  <caption class="sr-only">
                    Field coverage for {escape(type_report.name)}
                  </caption>
                  <thead>
                    <tr class="sr-only">
                      <th scope="col">Field</th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fields}
                  </tbody>
                </table>
              </section>"""


def _render_field(field_report: FieldCoverage) -> str:
    status = "covered" if field_report.covered else "missing"
    name = escape(field_report.name)
    return f"""
                    <tr
                      class="field-row"
                      data-status="{status}"
                      aria-label="{name}, {status}"
                    >
                      <th class="field-name-cell" scope="row">
                        <code>{name}</code>
                      </th>
                      <td class="field-state-cell">{status.title()}</td>
                    </tr>"""


def _coverage_tone(percentage: float) -> CoverageTone:
    if percentage >= _HIGH_COVERAGE:
        return "high"
    if percentage >= _LOW_COVERAGE:
        return "medium"
    return "low"


def _plural(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"
