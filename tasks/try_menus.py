"""Throwaway preview of the installer menus. Nothing real is installed or changed.

Usage: .venv/bin/python tasks/try_menus.py [--plain] [--prior] [--first-unit] [START]

START is main (default), unit_type_install, unit_type_additional, update or utilities.

  --plain       force the ANSI renderer even if `rich` is installed
  --prior       pretend a prior AFC install exists (shows the Update option)
  --first-unit  create a fake first unit so the "additional system" menu works
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from installer.platform_core.console import Console, Prompter  # noqa: E402
from installer.platform_core.context import Context  # noqa: E402
from installer.platform_core.errors import InstallerExit  # noqa: E402
from installer.ui_menus.menus import MENUS  # noqa: E402
from installer.ui_menus.navigation import MenuDeps, run_menus  # noqa: E402
from installer.ui_menus.renderer import AnsiRenderer  # noqa: E402
from installer.ui_menus.rich_renderer import choose_renderer  # noqa: E402
from installer.ui_menus.state import MenuState  # noqa: E402
from installer.unit_registry.selection import UnitSelection  # noqa: E402


class PreviewActions:
    """Reports what each action would do and sets the same flags the real ones do."""

    def _say(self, console: Console, text: str) -> None:
        console.print_msg("INFO", f"[preview] {text}")

    def __init__(self, console: Console) -> None:
        self.console = console

    def install(self, state: MenuState) -> None:
        self._say(self.console, f"would install {state.selection.installation_type}")
        state.ctx.files_updated_or_installed = True
        state.message = "[preview] install finished (nothing was written)"

    def install_additional(self, state: MenuState) -> None:
        self._say(self.console, f"would add unit {state.selection.unit_name}")

    def update(self, state: MenuState) -> None:
        self._say(self.console, "would update")
        state.update_message += "[preview] update finished\n"

    def uninstall(self, state: MenuState) -> None:
        self._say(self.console, "would uninstall")

    def delete_var_file(self, state: MenuState) -> str:
        return "[preview] would remove AFC.var.unit\n"

    def rename_unit(self, state: MenuState) -> str:
        return "[preview] would rename a unit"

    def exit(self, state: MenuState) -> None:
        raise InstallerExit(0)


def main() -> int:
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    start = next((a for a in args if not a.startswith("--")), "main")
    home = Path(tempfile.mkdtemp(prefix="afc-preview-"))
    ctx = Context.create(afc_path=Path(__file__).resolve().parents[1], home=home)
    ctx.prior_installation = "--prior" in flags
    if "--first-unit" in flags:
        ctx.afc_config_dir.mkdir(parents=True)
        (ctx.afc_config_dir / "AFC_Turtle_1.cfg").write_text("[AFC_stepper lane1]\n")
    console = Console()
    renderer = AnsiRenderer(console) if "--plain" in flags else choose_renderer(
        console, sys.stdout.isatty()
    )
    deps = MenuDeps(console, Prompter(), renderer, PreviewActions(console))
    state = MenuState(ctx=ctx, selection=UnitSelection())
    print(f"Renderer: {type(renderer).__name__}  Sandbox: {home}")
    try:
        run_menus(start, state, deps, MENUS)
    except InstallerExit as exc:
        print(f"Exited with code {exc.code}")
        return exc.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
