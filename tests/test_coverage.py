from __future__ import annotations

import re

import graphql
import pytest

_COVERED_FIELD_COUNT = 2
_DISTINCT_SCHEMA_COUNT = 2
_NON_OBVIOUS_RESOLUTION_COUNT = 4
_TERMINAL_WIDTH = 72


def test_resolver_coverage_is_the_default(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class User:
            name: str

            @strawberry.field
            def greeting(self) -> str:
                return f"Hello {self.name}"

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> User:
                return User(name="Patrick")

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync("{ user { name } }")
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    output = result.stdout.str()
    assert "┌" in output
    assert "│ Python type" in output
    assert "│ All types" in output
    assert "└" in output
    result.stdout.fnmatch_lines(
        [
            "*Query*1*0*100.00%*",
            "*User*1*1*0.00%*greeting*",
            "*Overall coverage: 50.00% (1/2 fields, 1 missing)*",
        ]
    )


def test_all_fields_mode_includes_default_resolution(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class User:
            name: str

            @strawberry.field
            def greeting(self) -> str:
                return f"Hello {self.name}"

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> User:
                return User(name="Patrick")

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync("{ user { name } }")
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-mode=all",
        "--strawberry-coverage-html=htmlstrawberry",
        "-q",
    )

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Query*1*0*100.00%*",
            "*User*2*1*50.00%*greeting*",
            "*Overall coverage: 66.67% (2/3 fields, 1 missing)*",
        ]
    )
    html = (pytester.path / "htmlstrawberry" / "index.html").read_text()
    assert 'id="hide-fully-covered"' in html
    assert 'id="show-excluded-fields"' not in html
    assert not re.search(r'<tr\s+class="field-row"\s+data-status="excluded"', html)


def test_report_uses_python_names_and_shows_explicit_graphql_aliases(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type(name="PublicUser")
        class UserModel:
            @strawberry.field
            def display_name(self) -> str:
                return "Patrick"

            @strawberry.field(name="legacyLabel")
            def legacy_label(self) -> str:
                return "Patrick"

        @strawberry.type(name="RootQuery")
        class QueryRoot:
            @strawberry.field
            def current_user(self) -> UserModel:
                return UserModel()

        schema = strawberry.Schema(query=QueryRoot)

        def test_query() -> None:
            result = schema.execute_sync("{ currentUser { __typename } }")
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    output = result.stdout.str()
    assert "QueryRoot [RootQuery]" in output
    assert "UserModel [PublicUser]" in output
    assert "display_name, legacy_label [legacyLabel]" in output
    assert "displayName" not in output


def test_html_report_is_self_contained_and_uses_python_names(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type(name="User")
        class UserModel:
            role: str = "admin"

            @strawberry.field
            def display_name(self) -> str:
                return "Ada"

            @strawberry.field(name="email")
            def email_address(self) -> str:
                return "ada@example.com"

        @strawberry.type(name="Query")
        class QueryRoot:
            @strawberry.field
            def viewer(self) -> UserModel:
                return UserModel()

        schema = strawberry.Schema(query=QueryRoot)

        def test_query() -> None:
            result = schema.execute_sync("{ viewer { displayName } }")
            assert result.data == {"viewer": {"displayName": "Ada"}}
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-html=reports/strawberry",
        "-q",
    )

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*HTML report: reports/strawberry/index.html*"])
    html = (pytester.path / "reports" / "strawberry" / "index.html").read_text()
    assert "<!doctype html>" in html
    assert "<style>" in html
    assert "<script" not in html
    assert "prefers-color-scheme: dark" in html
    assert "position: sticky" in html
    assert "66.67%" in html
    assert "<h1>Strawberry coverage</h1>" in html
    assert "subscriptions" not in html.lower()
    assert "QueryRoot [Query]" in html
    assert "UserModel [User]" in html
    assert 'id="hide-fully-covered"' in html
    assert 'name="hide-fully-covered"' in html
    assert 'id="show-excluded-fields"' in html
    assert 'name="show-excluded-fields"' in html
    assert "Show excluded fields" in html
    excluded_control = re.search(
        r'<input\s+id="show-excluded-fields"(?P<attributes>.*?)>',
        html,
        re.DOTALL,
    )
    assert excluded_control is not None
    assert "checked" not in excluded_control.group("attributes")
    assert 'data-fully-covered="true"' in html
    assert 'data-status="excluded"' in html
    assert '<div class="type-columns" aria-hidden="true">' in html
    assert "<details" not in html
    assert 'class="type-header-row"' in html
    assert '<table class="field-table">' in html
    assert 'class="field-resolution"' not in html
    assert "Python type" not in html
    assert "Python field" not in html
    assert ">Covered<" not in html
    assert ">Missing<" not in html
    assert 'aria-label="viewer, covered"' in html
    assert 'aria-label="display_name, covered"' in html
    assert 'aria-label="email_address [email], missing"' in html
    assert 'aria-label="role, not counted"' in html
    assert '<td class="field-status-cell">missing</td>' in html
    assert '<td class="field-status-cell">not counted</td>' in html
    assert html.count('<td class="field-status-cell"></td>') == _COVERED_FIELD_COUNT
    assert 'class="summary-score" data-tone="medium"' in html
    assert "2/3 fields covered" in html
    assert 'class="schema-identity"' not in html
    role_location = re.search(
        r'<code>role</code>.*?class="field-location" '
        r'aria-label="([^"]+), line (\d+)"',
        html,
        re.DOTALL,
    )
    assert role_location is not None
    relative_path, line_number = role_location.groups()
    source_line = (
        (pytester.path / relative_path).read_text().splitlines()[int(line_number) - 1]
    )
    assert source_line.strip() == 'role: str = "admin"'
    assert "Resolvers only" in html


def test_html_report_write_failure_fails_the_run(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("def test_passes(): pass")
    report_directory = pytester.path / "not-a-directory"
    report_directory.write_text("file")

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        f"--strawberry-coverage-html={report_directory}",
        "-q",
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*HTML report: failed to write*"])


def test_html_report_marks_excluded_only_types_as_not_scored(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class Profile:
            name: str

        @strawberry.type
        class Query:
            @strawberry.field
            def profile(self) -> Profile:
                return Profile(name="Ada")

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync("{ profile { name } }")
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-html=htmlstrawberry",
        "-q",
    )

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*Overall coverage: 100.00% (1/1 fields, 0 missing)*"])
    assert "│ Profile" not in result.stdout.str()
    html = (pytester.path / "htmlstrawberry" / "index.html").read_text()
    profile = re.search(
        r'<section\s+class="type"\s+data-fully-covered="false"\s+'
        r'data-only-excluded="true".*?aria-label="Profile,\s+not scored,\s+'
        r'0 fields, 0 missing".*?type-percentage-empty">—</span>',
        html,
        re.DOTALL,
    )
    assert profile is not None
    assert "Show excluded fields" in html
    assert '<span class="report-control-count">(1)</span>' in html


def test_html_report_identifies_non_obvious_field_resolution(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry
        from strawberry.extensions import FieldExtension

        def external_resolver() -> str:
            return "external"

        def make_resolver(value: str):
            def resolver() -> str:
                return value

            return resolver

        class AuditExtension(FieldExtension):
            def resolve(self, next_, source, info, **kwargs):
                return next_(source, info, **kwargs)

        @strawberry.type
        class Query:
            @strawberry.field
            def inline(self) -> str:
                return "inline"

            external: str = strawberry.field(resolver=external_resolver)
            generated: str = strawberry.field(resolver=make_resolver("generated"))
            anonymous: str = strawberry.field(resolver=lambda: "anonymous")
            extended: str = strawberry.field(
                resolver=external_resolver,
                extensions=[AuditExtension()],
            )

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync(
                "{ inline external generated anonymous extended }"
            )
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-html=htmlstrawberry",
        "-q",
    )

    result.assert_outcomes(passed=1)
    report_directory = pytester.path / "htmlstrawberry"
    html = (report_directory / "index.html").read_text()
    assert 'aria-label="inline, covered"' in html
    assert "via external_resolver" in html
    assert "via make_resolver(...)" in html
    assert "via lambda" in html
    assert "via external_resolver · AuditExtension" in html
    assert html.count('class="field-resolution"') == _NON_OBVIOUS_RESOLUTION_COUNT
    external_location = re.search(
        r'<code>external</code>.*?class="field-location" '
        r'aria-label="([^"]+), line (\d+)"',
        html,
        re.DOTALL,
    )
    assert external_location is not None
    relative_path, line_number = external_location.groups()
    source_line = (
        (pytester.path / relative_path).read_text().splitlines()[int(line_number) - 1]
    )
    assert source_line.strip().startswith("external: str = strawberry.field")
    assert not list(report_directory.glob("source-*.html"))


def test_html_report_locates_inherited_field_declarations(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class BaseQuery:
            @strawberry.field
            def inherited(self) -> str:
                return "inherited"

        @strawberry.type
        class Query(BaseQuery):
            @strawberry.field
            def local(self) -> str:
                return "local"

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync("{ inherited local }")
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-html=htmlstrawberry",
        "-q",
    )

    result.assert_outcomes(passed=1)
    html = (pytester.path / "htmlstrawberry" / "index.html").read_text()
    inherited_location = re.search(
        r'<code>inherited</code>.*?class="field-location" '
        r'aria-label="([^"]+), line (\d+)"',
        html,
        re.DOTALL,
    )
    assert inherited_location is not None
    relative_path, line_number = inherited_location.groups()
    source_line = (
        (pytester.path / relative_path).read_text().splitlines()[int(line_number) - 1]
    )
    assert source_line.strip() == "def inherited(self) -> str:"


def test_html_report_rejects_an_empty_directory(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-html=",
        "-q",
    )

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*must be a non-empty directory*"])
    assert not (pytester.path / "index.html").exists()


def test_report_wraps_long_missing_fields_to_the_terminal_width(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COLUMNS", str(_TERMINAL_WIDTH))
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def covered(self) -> str:
                return "covered"

            @strawberry.field(
                name="thisIsAVeryLongUncoveredGraphqlFieldNameThatWraps"
            )
            def uncovered(self) -> str:
                return "missing"

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync("{ covered }")
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    table_lines = [
        line
        for line in result.stdout.str().splitlines()
        if line.startswith(("┌", "│", "├", "└"))
    ]
    assert table_lines
    assert all(len(line) <= _TERMINAL_WIDTH for line in table_lines)
    assert "uncovered [thisIsAVeryLongUn" in result.stdout.str()
    assert "coveredGraphqlFieldNameThatW" in result.stdout.str()


def test_only_invoked_fields_count_and_raised_resolvers_count(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def ok(self) -> str:
                return "ok"

            @strawberry.field
            def skipped(self) -> str:
                return "skipped"

            @strawberry.field
            def failure(self) -> str:
                raise ValueError("expected")

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync(
                "{ ok skipped @skip(if: true) failure }"
            )
            assert result.errors is not None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Query*3*1*66.67%*skipped*",
            "*Overall coverage: 66.67% (2/3 fields, 1 missing)*",
        ]
    )


def test_concrete_interface_fields_are_discovered(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.interface
        class Node:
            id: strawberry.ID

        @strawberry.type
        class User(Node):
            name: str

            @strawberry.field
            def greeting(self) -> str:
                return "hello"

        @strawberry.type
        class Query:
            @strawberry.field
            def node(self) -> Node:
                return User(id=strawberry.ID("1"), name="Patrick")

        schema = strawberry.Schema(query=Query, types=[User])

        def test_query() -> None:
            result = schema.execute_sync(
                "{ node { id ... on User { name } } }"
            )
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Query*1*0*100.00%*",
            "*User*1*1*0.00%*greeting*",
            "*Overall coverage: 50.00% (1/2 fields, 1 missing)*",
        ]
    )


def test_union_members_are_discovered(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        from typing import Annotated, Union

        import strawberry

        @strawberry.type
        class User:
            @strawberry.field
            def label(self) -> str:
                return "user"

        @strawberry.type
        class Team:
            @strawberry.field
            def label(self) -> str:
                return "team"

        SearchResult = Annotated[
            Union[User, Team], strawberry.union("SearchResult")
        ]

        @strawberry.type
        class Query:
            @strawberry.field
            def search(self) -> SearchResult:
                return User()

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync(
                "{ search { ... on User { label } } }"
            )
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Query*1*0*100.00%*",
            "*Team*1*1*0.00%*label*",
            "*User*1*0*100.00%*",
            "*Overall coverage: 66.67% (2/3 fields, 1 missing)*",
        ]
    )


def test_async_mutations_are_collected(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import asyncio

        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def status(self) -> str:
                return "ok"

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            async def update(self) -> bool:
                await asyncio.sleep(0)
                return True

        schema = strawberry.Schema(query=Query, mutation=Mutation)

        def test_operations() -> None:
            assert schema.execute_sync("{ status }").errors is None
            result = asyncio.run(schema.execute("mutation { update }"))
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Mutation*1*0*100.00%*",
            "*Query*1*0*100.00%*",
            "*Overall coverage: 100.00% (2/2 fields, 0 missing)*",
        ]
    )


def test_null_short_circuit_does_not_cover_nested_fields(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class Child:
            @strawberry.field
            def nested(self) -> str:
                return "nested"

        @strawberry.type
        class Query:
            @strawberry.field
            def child(self) -> Child | None:
                return None

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync(
                "query { alias: child { ...Nested } } "
                "fragment Nested on Child { nested }"
            )
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Child*1*1*0.00%*nested*",
            "*Query*1*0*100.00%*",
            "*Overall coverage: 50.00% (1/2 fields, 1 missing)*",
        ]
    )


def test_existing_extension_order_and_result_are_preserved(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry
        from strawberry.extensions import SchemaExtension

        events: list[str] = []

        class First(SchemaExtension):
            def resolve(self, next_, root, info, *args, **kwargs):
                events.append("first before")
                result = next_(root, info, *args, **kwargs)
                events.append("first after")
                return result

        class Second(SchemaExtension):
            def resolve(self, next_, root, info, *args, **kwargs):
                events.append("second before")
                result = next_(root, info, *args, **kwargs)
                events.append("second after")
                return result

        @strawberry.type
        class Query:
            @strawberry.field
            def value(self) -> str:
                events.append("resolver")
                return "value"

        schema = strawberry.Schema(query=Query, extensions=[First, Second])

        def test_query() -> None:
            result = schema.execute_sync("{ value }")
            assert result.data == {"value": "value"}
            assert events == [
                "second before",
                "first before",
                "resolver",
                "first after",
                "second after",
            ]
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*Overall coverage: 100.00% (1/1 fields, 0 missing)*"])


def test_fail_under_fails_an_otherwise_passing_run(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_passes() -> None:
            pass
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-fail-under=1",
        "--strawberry-coverage-html=htmlstrawberry",
        "-q",
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*No Strawberry schemas were observed.*",
            "*Overall coverage: 0.00% (0/0 fields, 0 missing)*",
            "*Coverage threshold: not met (0.00% < 1.00%)*",
        ]
    )
    html = (pytester.path / "htmlstrawberry" / "index.html").read_text()
    assert "Coverage threshold not met." in html


@pytest.mark.parametrize(
    ("threshold", "expected_exit"),
    [("66.67", pytest.ExitCode.OK), ("66.68", pytest.ExitCode.TESTS_FAILED)],
)
def test_fail_under_uses_the_displayed_two_decimal_percentage(
    pytester: pytest.Pytester,
    threshold: str,
    expected_exit: pytest.ExitCode,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def one(self) -> str:
                return "one"

            @strawberry.field
            def two(self) -> str:
                return "two"

            @strawberry.field
            def three(self) -> str:
                return "three"

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            assert schema.execute_sync("{ one two }").errors is None
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        f"--strawberry-coverage-fail-under={threshold}",
        "-q",
    )

    assert result.ret == expected_exit
    result.stdout.fnmatch_lines(["*Overall coverage: 66.67% (2/3 fields, 1 missing)*"])


@pytest.mark.parametrize(
    "option",
    [
        "--strawberry-coverage-mode=all",
        "--strawberry-coverage-fail-under=50",
        "--strawberry-coverage-html=htmlstrawberry",
    ],
)
def test_coverage_options_require_enable_flag(
    pytester: pytest.Pytester, option: str
) -> None:
    pytester.makepyfile("def test_passes(): pass")

    result = pytester.runpytest_subprocess(option, "-q")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*require --strawberry-coverage*"])


@pytest.mark.parametrize("value", ["-1", "101", "nan", "not-a-number"])
def test_fail_under_rejects_invalid_percentages(
    pytester: pytest.Pytester, value: str
) -> None:
    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        f"--strawberry-coverage-fail-under={value}",
        "-q",
    )

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*must be a number between 0 and 100*"])


def test_observed_schema_with_no_resolvers_is_fully_covered(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class Query:
            value: str = "value"

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            result = schema.execute_sync("{ value }", root_value=Query())
            assert result.errors is None
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-fail-under=100",
        "-q",
    )

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*Overall coverage: 100.00% (0/0 fields, 0 missing)*"])


def test_distinct_schemas_get_separate_tables(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class FirstQuery:
            @strawberry.field
            def first(self) -> str:
                return "first"

        @strawberry.type
        class SecondQuery:
            @strawberry.field
            def second(self) -> str:
                return "second"

        first_schema = strawberry.Schema(query=FirstQuery)
        second_schema = strawberry.Schema(query=SecondQuery)

        def test_schemas() -> None:
            assert first_schema.execute_sync("{ first }").errors is None
            assert second_schema.execute_sync("{ second }").errors is None
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-html=htmlstrawberry",
        "-q",
    )

    result.assert_outcomes(passed=1)
    assert result.stdout.str().count("Schema ") == _DISTINCT_SCHEMA_COUNT
    result.stdout.fnmatch_lines(["*Overall coverage: 100.00% (2/2 fields, 0 missing)*"])
    html = (pytester.path / "htmlstrawberry" / "index.html").read_text()
    assert html.count('class="schema-identity"') == _DISTINCT_SCHEMA_COUNT
    assert ">Schema 1</h2>" in html
    assert ">Schema 2</h2>" in html


def test_python_metadata_keeps_identical_graphql_field_sets_separate(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type(name="Query")
        class FirstRoot:
            @strawberry.field(name="value")
            def first_value(self) -> str:
                return "first"

        @strawberry.type(name="Query")
        class SecondRoot:
            @strawberry.field(name="value")
            def second_value(self) -> str:
                return "second"

        first_schema = strawberry.Schema(query=FirstRoot)
        second_schema = strawberry.Schema(query=SecondRoot)

        def test_schemas() -> None:
            assert first_schema.execute_sync("{ value }").errors is None
            assert second_schema.execute_sync("{ value }").errors is None
        """
    )

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    output = result.stdout.str()
    assert output.count("Schema ") == _DISTINCT_SCHEMA_COUNT
    assert "FirstRoot [Query]" in output
    assert "SecondRoot [Query]" in output
    result.stdout.fnmatch_lines(["*Overall coverage: 100.00% (2/2 fields, 0 missing)*"])


def test_subscription_coverage_matches_graphql_core_capability(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import asyncio
        from collections.abc import AsyncGenerator

        import strawberry

        @strawberry.type
        class Payload:
            value: int

            @strawberry.field
            def doubled(self) -> int:
                return self.value * 2

        @strawberry.type
        class Query:
            status: str = "ok"

        @strawberry.type
        class Subscription:
            @strawberry.subscription
            async def item(self) -> AsyncGenerator[Payload, None]:
                yield Payload(value=2)

        schema = strawberry.Schema(query=Query, subscription=Subscription)

        async def consume() -> None:
            stream = await schema.subscribe(
                "subscription { item { value doubled } }"
            )
            result = await anext(stream)
            assert result.data == {"item": {"value": 2, "doubled": 4}}
            await stream.aclose()

        def test_subscription() -> None:
            query_result = schema.execute_sync(
                "{ status }", root_value=Query()
            )
            assert query_result.errors is None
            asyncio.run(consume())
        """
    )

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-mode=all",
        "--strawberry-coverage-html=htmlstrawberry",
        "-n",
        "2",
        "-q",
    )

    result.assert_outcomes(passed=1)
    html = (pytester.path / "htmlstrawberry" / "index.html").read_text()
    if (graphql.version_info.major, graphql.version_info.minor) >= (3, 3):
        result.stdout.fnmatch_lines(
            [
                "*Subscriptions: included*",
                "*Overall coverage: 100.00% (4/4 fields, 0 missing)*",
            ]
        )
        assert "subscriptions included" in html.lower()
        assert "did not contribute" not in result.stdout.str()
    else:
        result.stdout.fnmatch_lines(
            [
                "*Subscriptions: excluded*",
                "*Overall coverage: 100.00% (1/1 fields, 0 missing)*",
                "*WARNING: Subscription executions did not contribute*",
            ]
        )
        assert "subscriptions excluded" in html.lower()


def test_collect_only_suppresses_reporting_and_gating(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile("def test_example(): pass")

    result = pytester.runpytest_subprocess(
        "--strawberry-coverage",
        "--strawberry-coverage-fail-under=100",
        "--strawberry-coverage-html=htmlstrawberry",
        "--collect-only",
        "-q",
    )

    assert result.ret == pytest.ExitCode.OK
    assert "Strawberry coverage" not in result.stdout.str()
    assert not (pytester.path / "htmlstrawberry").exists()


def test_plugin_is_inert_without_enable_flag(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def value(self) -> str:
                return "value"

        schema = strawberry.Schema(query=Query)

        def test_query() -> None:
            assert schema.execute_sync("{ value }").errors is None
        """
    )

    result = pytester.runpytest_subprocess("-q")

    result.assert_outcomes(passed=1)
    assert "Strawberry coverage" not in result.stdout.str()


def test_xdist_workers_merge_complementary_coverage(
    pytester: pytest.Pytester,
) -> None:
    pytester.makeconftest(
        """
        import strawberry

        def resolve_one() -> str:
            return "one"

        @strawberry.type
        class Query:
            default_value: str = "default"
            one: str = strawberry.field(resolver=resolve_one)

            @strawberry.field
            def two(self) -> str:
                return "two"

        schema = strawberry.Schema(query=Query)
        """
    )
    pytester.makepyfile(
        test_one="""
        from conftest import schema

        def test_one() -> None:
            assert schema.execute_sync("{ one }").errors is None
        """,
        test_two="""
        from conftest import schema

        def test_two() -> None:
            assert schema.execute_sync("{ two }").errors is None
        """,
    )

    result = pytester.runpytest_subprocess(
        "-n2",
        "--strawberry-coverage",
        "--strawberry-coverage-fail-under=100",
        "--strawberry-coverage-html=htmlstrawberry",
        "-q",
    )

    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(["*Overall coverage: 100.00% (2/2 fields, 0 missing)*"])
    html = (pytester.path / "htmlstrawberry" / "index.html").read_text()
    assert "100.00%" in html
    assert "2/2 fields covered" in html
    assert "via resolve_one" in html
    assert 'aria-label="default_value, not counted"' in html
    assert 'aria-label="conftest.py, line ' in html
