"""Tests for NightOwl board selection and additional-unit MCU naming."""
from __future__ import annotations

from pathlib import Path

import pytest

from test_shared_buffer import REPO_ROOT, run_bash

MENU_PRELUDE = r"""
clear() { :; }
print_unit_art() { :; }
unit_print_install_menu_options() { :; }
unit_print_additional_menu_row() { :; }
check_existing_unit_installed() { return 0; }
main_menu() { exit 0; }
install_afc() { :; }
exit_afc_install() { echo "FINAL board=$nightowl_board_type"; exit 0; }
files_updated_or_installed="False"
installation_options=("NightOwl")
installation_type="NightOwl"
"""


def run_menu(menu: str, keys: list[str], board: str = "ERB_2.0") -> str:
    body = MENU_PRELUDE + f'nightowl_board_type="{board}"\n{menu}\n'
    result = run_bash(body, stdin="\n".join(keys + ["Q"]) + "\n")
    assert result.returncode == 0, result.stderr
    return result.stdout


class TestIndexOf:
    def test_returns_index_of_value(self) -> None:
        out = run_bash('arr=(a b c)\nindex_of arr c').stdout
        assert out == "2\n"

    def test_returns_zero_when_value_missing(self) -> None:
        out = run_bash('arr=(a b c)\nindex_of arr nope').stdout
        assert out == "0\n"


@pytest.mark.parametrize("menu", ["install_menu", "additional_system_menu"])
class TestNightOwlBoardCycle:
    def test_first_press_changes_board_after_other_board_cycled(self, menu: str) -> None:
        # D cycles the HTLF board and advances the shared board_counter.
        out = run_menu(menu, ["D", "J"])
        assert "FINAL board=OWLFC_Mini" in out
        assert "NightOwl Board Type: OWLFC_Mini" in out

    def test_cycle_starts_from_preselected_board(self, menu: str) -> None:
        out = run_menu(menu, ["J"], board="OWLFC_Mini")
        assert "FINAL board=ERB_2.0" in out
        assert "NightOwl Board Type: ERB_2.0" in out

    def test_two_presses_return_to_start(self, menu: str) -> None:
        out = run_menu(menu, ["J", "J"])
        assert "FINAL board=ERB_2.0" in out


class TestAdditionalNightOwlMcu:
    BODY = r"""
installation_type="NightOwl"; boxturtle_name="Owl_2"; is_additional_unit="True"
nightowl_board_type="%s"
install_additional_unit
echo "=== FILES ==="; ls "$afc_config_dir/mcu"
echo "=== MCU ==="; cat "$afc_config_dir/mcu/%s_Owl_2.cfg"
echo "=== UNIT ==="; cat "$afc_config_dir/AFC_Owl_2.cfg"
"""

    @pytest.mark.parametrize("board", ["ERB_2.0", "OWLFC_Mini"])
    def test_mcu_file_is_renamed_for_the_unit(self, board: str) -> None:
        out = run_bash(self.BODY % (board, board)).stdout
        mcu = out.split("=== MCU ===")[1].split("=== UNIT ===")[0]
        assert f"{board}_Owl_2.cfg\n" in out.split("=== MCU ===")[0]
        assert "[board_pins Owl_2]\n" in mcu
        assert "mcu: Owl_2" in mcu
        assert "NightOwl" not in mcu

    @pytest.mark.parametrize("board", ["ERB_2.0", "OWLFC_Mini"])
    def test_unit_file_includes_the_renamed_mcu_file(self, board: str) -> None:
        out = run_bash(self.BODY % (board, board)).stdout
        unit = out.split("=== UNIT ===")[1]
        assert f"[include mcu/{board}_Owl_2.cfg]\n" in unit
        assert f"[include mcu/{board}.cfg]" not in unit
        assert "[mcu Owl_2]\n" in unit

    def test_first_unit_keeps_shared_mcu_file(self) -> None:
        body = r"""
installation_type="NightOwl"; boxturtle_name="NightOwl_1"; nightowl_board_type="OWLFC_Mini"
copy_unit_files
ls "$afc_config_dir/mcu"
grep -c "include mcu/OWLFC_Mini.cfg" "$afc_config_dir/AFC_NightOwl_1.cfg"
"""
        out = run_bash(body).stdout
        assert out == "OWLFC_Mini.cfg\n1\n"


class TestOwlfcMiniConfig:
    def read(self, rel: str) -> str:
        return (REPO_ROOT / rel).read_text()

    def test_mcu_file_defines_rgb_alias(self) -> None:
        assert "RGB1=PB3" in self.read("config/mcu/OWLFC_Mini.cfg")

    def test_mcu_file_has_no_lane_sections(self) -> None:
        mcu = self.read("config/mcu/OWLFC_Mini.cfg")
        assert "tmc2209" not in mcu
        assert "sense_resistor" not in mcu
        assert "lane" not in mcu

    def test_template_carries_sense_resistor_for_both_lanes(self) -> None:
        tmpl = self.read("templates/AFC_NightOwl_1-OWLFC_Mini.cfg")
        for lane in ("lane1", "lane2"):
            section = tmpl.split(f"[tmc2209 AFC_stepper {lane}]")[1].split("\n\n")[0]
            assert "sense_resistor: 0.180" in section
        assert tmpl.count("sense_resistor: 0.180") == 2
