from types import ModuleType

import pytest


def test_plugin_is_registered(pytestconfig: pytest.Config) -> None:
    plugin = pytestconfig.pluginmanager.get_plugin("pytest-strawberry")

    assert isinstance(plugin, ModuleType)
    assert plugin.__name__ == "pytest_strawberry.plugin"
