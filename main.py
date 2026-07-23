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

CSS_PATH = Path(__file__).parent / "src" / "style" / "style.tcss"
env_path = Path(".env")

if not env_path.exists():
    env_path.touch()
    print("Created a new .env file for your configuration information.")

class MainApp(App):
    TITLE = "Test Course Reset Utility"
    BINDINGS = [
            Binding("up", "focus_previous", "Previous", show=False, priority=True),
            Binding("down", "focus_next", "Next", show=False, priority=True),
            Binding("left", "focus_previous", "Previous", show=False, priority=True),
            Binding("right", "focus_next", "Next", show=False, priority=True),
        ]
    CSS_PATH = CSS_PATH
    ENABLE_COMMAND_PALETTE = False

    def on_mount(self) -> None:
        """Load initial environment variables into app attributes on startup."""
        load_dotenv(dotenv_path=env_path)
        self.load_config_vars()

    def load_config_vars(self) -> None:
        """Helper to load or refresh environment variables onto self."""
        self.subdomain = os.getenv("SUBDOMAIN", "")
        self.api_key = os.getenv("API_KEY", "")
        self.target_course = os.getenv("TARGET_COURSE_ID", "")
        self.source_course = os.getenv("SOURCE_COURSE_ID", "")

    def action_quit_app(self):
        self.exit(0)

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Label("Test Course Reset Utility")
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
            def handle_config_dismiss(result):
                # This runs automatically after ConfigModal closes
                load_dotenv(dotenv_path=env_path, override=True)
                self.load_config_vars()
                self.notify("Configuration reloaded successfully.", title="Updated", severity="information", timeout=3)

            self.push_screen(ConfigModal(), handle_config_dismiss)
        elif event.button.id == "reset_default":
            if not all([self.subdomain, self.api_key, self.target_course, self.source_course]):
                self.notify(
                    "Configuration not properly set. Click the configuration button to fix that.",
                    title="Error",
                    severity="warning",
                    timeout=5,
                )
                return
            self.run_worker(self._faked_reset(self.try_course_reset))
        elif event.button.id == "reset_other":
            if not all([self.subdomain, self.api_key, self.target_course, self.source_course]):
                self.notify(
                    "Configuration not properly set. Click the configuration button to fix that.",
                    title="Error",
                    severity="warning",
                    timeout=5,
                )
                return
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
