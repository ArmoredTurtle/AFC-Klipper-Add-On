"""
Unit tests for extras/AFC_NightOwl.py

Covers:
  - afcNightOwl: is a subclass of afcBoxTurtle
  - afcNightOwl.__init__: reads type from config
  - afcNightOwl.handle_connect: calls super, sets Night Owl logo strings
  - load_config_prefix: Klipper config entry point
"""

from __future__ import annotations

import configparser
import importlib.util
import sys
from typing import Optional
from unittest.mock import patch
import pytest

from extras.AFC_NightOwl import afcNightOwl, load_config_prefix
from extras.AFC_BoxTurtle import afcBoxTurtle


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_night_owl_config(name: str="NightOwl_1", values: Optional[dict]=None):
    """Build the MockConfig/MockPrinter/MockAFC trio needed to construct an
    afcNightOwl via its real __init__ (chained through afcBoxTurtle.__init__
    and afcUnit.__init__).

    :param name: Unit name to use for the config section
    :param values: Config values to seed, merged over the defaults
    :return tuple: (config, printer, afc) mocks ready to build an afcNightOwl
    """
    from tests.conftest import MockAFC, MockConfig, MockPrinter

    afc = MockAFC()
    printer = MockPrinter(afc=afc)
    config = MockConfig(name=f"AFC_NightOwl {name}", printer=printer, values=values or {})
    return config, printer, afc


def _make_night_owl(name: str="NightOwl_1", values: Optional[dict]=None) -> afcNightOwl:
    """Build a real afcNightOwl via its actual __init__.

    :param name: Unit name to use for the config section
    :param values: Config values to seed, merged over the defaults
    :return afcNightOwl: constructed Night Owl unit
    """
    config, printer, afc = _make_night_owl_config(name=name, values=values)
    return afcNightOwl(config)


# ── Inheritance ───────────────────────────────────────────────────────────────

class TestNightOwlInheritance:
    def test_is_subclass_of_box_turtle(self) -> None:
        assert issubclass(afcNightOwl, afcBoxTurtle)

    def test_instance_is_box_turtle(self) -> None:
        unit = _make_night_owl()
        assert isinstance(unit, afcBoxTurtle)


# ── __init__ ──────────────────────────────────────────────────────────────────

class TestNightOwlInit:
    def test_type_defaults_to_night_owl_when_not_set_in_config(self) -> None:
        unit = _make_night_owl()
        assert unit.type == "Night_Owl"

    def test_type_reads_overridden_value_from_config(self) -> None:
        unit = _make_night_owl(values={"type": "CustomOwl"})
        assert unit.type == "CustomOwl"


# ── handle_connect ────────────────────────────────────────────────────────────

class TestNightOwlHandleConnect:
    def test_calls_super_handle_connect_once(self) -> None:
        unit = _make_night_owl()
        with patch.object(afcBoxTurtle, "handle_connect") as mock_super:
            unit.handle_connect()
        mock_super.assert_called_once_with()

    def test_sets_exact_logo_after_super_runs(self) -> None:
        """afcNightOwl must overwrite whatever afcBoxTurtle.handle_connect set
        self.logo to, proving the override actually replaces (not just adds
        to) the inherited logo."""
        unit = _make_night_owl()

        def fake_super_handle_connect(self) -> None:
            self.logo = "sentinel-from-box-turtle"
            self.logo_error = "sentinel-error-from-box-turtle"

        with patch.object(afcBoxTurtle, "handle_connect", fake_super_handle_connect):
            unit.handle_connect()

        expected_logo = ('<span class=success--text>R  ,     ,\n'
                         'E  )\\___/(\n'
                         'A {(@)v(@)}\n'
                         'D  {|~~~|}\n'
                         'Y  {/^^^\\}\n'
                         '!   `m-m`</span>\n')
        assert unit.logo == expected_logo

    def test_sets_exact_logo_error_after_super_runs(self) -> None:
        unit = _make_night_owl()

        def fake_super_handle_connect(self) -> None:
            self.logo = "sentinel-from-box-turtle"
            self.logo_error = "sentinel-error-from-box-turtle"

        with patch.object(afcBoxTurtle, "handle_connect", fake_super_handle_connect):
            unit.handle_connect()

        assert unit.logo_error == '<span class=error--text>Night Owl Not Ready</span>\n'


# ── load_config_prefix ────────────────────────────────────────────────────────

class TestNightOwlLoadConfigPrefix:
    def test_returns_afc_night_owl_instance(self) -> None:
        config, printer, afc = _make_night_owl_config()

        unit = load_config_prefix(config)

        assert isinstance(unit, afcNightOwl)

    def test_passes_config_through_to_constructed_unit(self) -> None:
        config, printer, afc = _make_night_owl_config(values={"type": "CustomOwl"})

        unit = load_config_prefix(config)

        assert unit.type == "CustomOwl"


# ═════════════════════════════════════════════════════════════════════════
# Module-level import guards
# ═════════════════════════════════════════════════════════════════════════

def _exec_afc_night_owl_with_blocked_dependency(blocked_module_name: str) -> None:
    """Execute a throw-away copy of extras/AFC_NightOwl.py's module-level
    code with `blocked_module_name` forced to fail import, to exercise the
    file's top-level ``try: from X import Y / except: raise error(...)``
    guards.

    Never touches the real, already-imported ``extras.AFC_NightOwl`` module
    that the rest of this test suite depends on: the copy is loaded under a
    throwaway module name and discarded afterward, whether or not it raises.
    Cleanup restores the exact same pre-existing module object in
    sys.modules so other test files' references stay valid.

    :param blocked_module_name: Dotted module name to force an ImportError for
    """
    import extras.AFC_NightOwl as real_module
    fresh_name = "extras.AFC_NightOwl_import_guard_probe"
    original_blocked_module = sys.modules.get(blocked_module_name)
    sys.modules[blocked_module_name] = None
    try:
        spec = importlib.util.spec_from_file_location(fresh_name, real_module.__file__)
        fresh = importlib.util.module_from_spec(spec)
        sys.modules[fresh_name] = fresh
        try:
            spec.loader.exec_module(fresh)
        finally:
            sys.modules.pop(fresh_name, None)
    finally:
        if original_blocked_module is not None:
            sys.modules[blocked_module_name] = original_blocked_module
        else:
            sys.modules.pop(blocked_module_name, None)


class TestModuleImportGuards:
    """Covers the two module-level `try/except: raise error(...)` guards in
    AFC_NightOwl.py, one per dependency import."""

    def test_afc_utils_error_str_import_failure_raises_configparser_error(self) -> None:
        """The first guard imports ERROR_STR itself from AFC_utils, so it
        can't use ERROR_STR.format(...) in its own except clause."""
        with pytest.raises(configparser.Error) as exc_info:
            _exec_afc_night_owl_with_blocked_dependency("extras.AFC_utils")
        assert str(exc_info.value).startswith(
            "Error when trying to import AFC_utils.ERROR_STR"
        )

    def test_afc_boxturtle_import_failure_raises_configparser_error(self) -> None:
        with pytest.raises(configparser.Error) as exc_info:
            _exec_afc_night_owl_with_blocked_dependency("extras.AFC_BoxTurtle")
        assert str(exc_info.value).startswith(
            "Error trying to import AFC_BoxTurtle, please rerun install-afc.sh"
        )
