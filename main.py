import os
from dotenv import load_dotenv, set_key
from pathlib import Path
import asyncio

from collections.abc import Iterable
from textual import on
from textual.app import App
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Header, Footer, Label, Button

from src.services.course_reset import course_reset
from src.screens.config_modal import ConfigModal
from src.screens.custom_reset_modal import CustomResetModal

env_path = Path(".env")

if not env_path.exists():
    env_path.touch()
    print("Created a new .env file for your configuration information.")

load_dotenv(dotenv_path=env_path)

class MainApp(App):
    BINDINGS = [
            Binding("up", "focus_previous", "Previous", show=False, priority=True),
            Binding("down", "focus_next", "Next", show=False, priority=True),
            Binding("left", "focus_previous", "Previous", show=False, priority=True),
            Binding("right", "focus_next", "Next", show=False, priority=True),
        ]
    CSS_PATH = "src/style/style.tcss"
    ENABLE_COMMAND_PALETTE = False

    def action_quit_app(self):
        self.exit(0)

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Label("Test Course Utility App")
        yield Button("Configuration", id="config")
        yield Button("Default Course Reset", id="reset_default")
        yield Button("Custom Course Reset", id="reset_other")
        yield Button("Quit", id="quit")
        yield Footer()

    @on(Button.Pressed, "#quit")
    def handle_quit(self) -> None:
        self.action_quit_app()

    @on(Button.Pressed)
    def handle_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "config":
            self.push_screen(ConfigModal())
        elif event.button.id == "reset_default":
            self.run_worker(self._faked_reset(self.try_course_reset))
        elif event.button.id == "reset_other":
            def handle_custom_modal_dismiss(result):
                if not result:
                    return
                target_course_id, source_course_id = result
                self.run_worker(
                    self._faked_reset(
                        lambda: self.try_course_reset(target_course_id, source_course_id)
                    )
                )

            self.push_screen(CustomResetModal(), handle_custom_modal_dismiss)

    def try_course_reset(
        self,
        target_course_id: str | None = None,
        source_course_id: str | None = None,
    ):
        try:
            new_course_id = course_reset(
                target_course_id=target_course_id,
                source_course_id=source_course_id,
            )

            subdomain = os.getenv("SUBDOMAIN")
            migration_url = f"https://{subdomain}.instructure.com/courses/{new_course_id}/content_migrations"

            set_key(env_path, "TARGET_COURSE_ID", str(new_course_id))
            os.environ["TARGET_COURSE_ID"] = str(new_course_id)

            self.notify(
                f'[link="{migration_url}"]Reset complete! Ctrl/Cmd + Click here to view migration status[/link]',
                title="Success",
                timeout=10,
            )

        except (ValueError, RuntimeError) as e:
            self.notify(str(e), title="Course Reset Error", severity="error")

    async def _faked_reset(self, reset_fn) -> None:
        screen = self.screen
        screen.loading = True
        try:
            await asyncio.to_thread(reset_fn)
        finally:
            screen.loading = False


if __name__ == "__main__":
    app = MainApp()
    app.run()
