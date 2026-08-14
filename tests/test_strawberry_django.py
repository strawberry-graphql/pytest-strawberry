from importlib.util import find_spec
from pathlib import Path

import pytest

_EXAMPLE = (
    Path(__file__).parents[1] / "examples" / "strawberry_django" / "test_schema.py"
)

pytestmark = pytest.mark.skipif(
    find_spec("strawberry_django") is None,
    reason="the strawberry-django example dependency group is not installed",
)


def test_generated_django_fields_use_custom_resolution(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(_EXAMPLE.read_text(encoding="utf-8"))

    result = pytester.runpytest_subprocess("--strawberry-coverage", "-q")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*FruitType*2*1*50.00%*description*",
            "*Query*1*0*100.00%*",
            "*Overall coverage: 66.67% (2/3 fields, 1 missing)*",
        ]
    )
