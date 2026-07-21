import os
from dotenv import load_dotenv, set_key
from pathlib import Path
from urllib.parse import urlparse

from collections.abc import Iterable
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Header, Footer, Label, Button, Input, Link, Select, RadioSet, RadioButton
from textual.screen import ModalScreen

from src.course_reset import course_reset
from src.get_course_candidates import get_course_candidates_by_name

env_path = Path(".env")

if not env_path.exists():
    env_path.touch()
    print("Created a new .env file for your configuration information.")

load_dotenv(dotenv_path=env_path)

class ConfigModal(ModalScreen):
    def compose(self) -> ComposeResult:
        # TODO Allow the user to Cancel, but save button needs to not let the user get past this screen if there's something empty

        subdomain = os.getenv("SUBDOMAIN", "")
        api_key = os.getenv("API_KEY", "")
        target_id = os.getenv("TARGET_COURSE_ID", "")
        source_id = os.getenv("SOURCE_COURSE_ID", "")

        yield Label("Configuration Settings", id="modal-title")

        # Subdomain section
        yield Label("Subdomain (e.g., 'yourschool' from yourschool.instructure.com):")
        yield Input(value=subdomain, id="SUBDOMAIN", placeholder="Enter subdomain...")

        # API Key section
        # TODO Make the link interactive
        yield Label("Developer Key:")
        yield Link("Click here for instructions", url="https://ed.link/community/how-to-set-up-developer-keys-in-canvas/")
        yield Input(value=api_key, id="API_KEY", placeholder="Enter Developer key...")

        # Target Course ID section
        yield Label("Target Course ID - The course you want to overwrite/reset (12345678 in yourschool.instructure.com/courses/12345678):")
        yield Input(value=target_id, id="TARGET_COURSE_ID", placeholder="Enter target course ID...")

        # Source Course ID section
        yield Label("Source Course ID - The template course to copy from (12345678 in yourschool.instructure.com/courses/12345678):")
        yield Input(value=source_id, id="SOURCE_COURSE_ID", placeholder="Enter source course ID...")

        yield Label("", id="error-message")

        # Action Buttons
        yield Button("Save & Close", id="save_config", variant="primary")
        yield Button("Cancel", id="cancel_config", variant="default")

    @on(Button.Pressed, "#cancel_config")
    def handle_cancel(self) -> None:
        self.dismiss()

    @on(Button.Pressed, "#save_config")
    def handle_save(self) -> None:
        subdomain_raw = self.query_one("#SUBDOMAIN", Input).value.strip()
        api_key = self.query_one("#API_KEY", Input).value.strip()
        target_id = self.query_one("#TARGET_COURSE_ID", Input).value.strip()
        source_id = self.query_one("#SOURCE_COURSE_ID", Input).value.strip()

        inputs = {
            "SUBDOMAIN": subdomain_raw,
            "API_KEY": api_key,
            "TARGET_COURSE_ID": target_id,
            "SOURCE_COURSE_ID": source_id,
        }

        # Check if any of the four are blank
        error_label = self.query_one("#error-message", Label)

        for key, value in inputs.items():
            if not value:
                error_label.update(f"Error: {key.replace('_', ' ').title()} cannot be blank!")
                return

        # 1. Shape Subdomain
        if "://" in subdomain_raw:
            parsed_url = urlparse(subdomain_raw)
            netloc = parsed_url.netloc
        else:
            netloc = subdomain_raw

        if netloc.endswith(".instructure.com"):
            subdomain_cleaned = netloc.split(".instructure.com")[0].split(".")[0]
        else:
            subdomain_cleaned = netloc

        if not subdomain_cleaned:
            error_label.update("Error: Invalid Subdomain format.")
            return

        inputs["SUBDOMAIN"] = subdomain_cleaned

        # 2. Data Validation for API Key
        if len(api_key) < 20:
            error_label.update("Error: API Key appears to be invalid (too short).")
            return

        # 3. Data Validation for Course IDs
        if not target_id.isdigit():
            error_label.update("Error: Target Course ID must be a valid number.")
            return

        if not source_id.isdigit():
            error_label.update("Error: Source Course ID must be a valid number.")
            return

        # Save all values to the .env file
        for key, value in inputs.items():
            set_key(env_path, key, value)
            os.environ[key] = value

        self.dismiss()

class CustomResetModal(ModalScreen):
    def __init__(self):
        super().__init__()
        self.step = 1
        self.default_target = os.getenv("TARGET_COURSE_ID", "")
        self.default_source = os.getenv("SOURCE_COURSE_ID", "")
        self.subdomain = os.getenv("SUBDOMAIN", "")
        self.api_key = os.getenv("API_KEY", "")

        self.target_course_id = None
        self.source_course_id = None

    def compose(self) -> ComposeResult:
        yield Label("Custom Course Reset", id="modal-title")

        yield Label(f"Target Course: Use default ({self.default_target}) or search a different one?", id="step-label")
        yield RadioSet(
            RadioButton("Use Default Target Course", id="target_default", value=True),
            RadioButton("Search for a Different Course", id="target_search"),
            id="target_choice_radios"
        )
        yield Input(placeholder="Enter target course name...", id="target_search_input", classes="hidden-input")
        yield Select([], id="target_select", prompt="Select correct target course", classes="hidden-select")

        yield Label(f"Source Course: Use default ({self.default_source}) or search a different one?", id="source-label", classes="hidden-widget")
        yield RadioSet(
            RadioButton("Use Default Source Course", id="source_default", value=True),
            RadioButton("Search for a Different Course", id="source_search"),
            id="source_choice_radios",
            classes="hidden-widget"
        )
        yield Input(placeholder="Enter source course name...", id="source_search_input", classes="hidden-input")
        yield Select([], id="source_select", prompt="Select correct source course", classes="hidden-select")

        yield Label("", id="error-message")
        yield Button("Next", id="next_btn", variant="primary")
        yield Button("Cancel", id="cancel_btn")

    @on(RadioSet.Changed)
    def handle_radio_change(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "target_choice_radios":
            is_search = event.pressed.id == "target_search"
            self.query_one("#target_search_input", Input).set_class(not is_search, "hidden-input")
        elif event.radio_set.id == "source_choice_radios":
            is_search = event.pressed.id == "source_search"
            self.query_one("#source_search_input", Input).set_class(not is_search, "hidden-input")

    @on(Button.Pressed, "#next_btn")
    def handle_next(self) -> None:
        error_label = self.query_one("#error-message", Label)
        error_label.update("")

        if self.step == 1:
            is_default = self.query_one("#target_default", RadioButton).value
            if is_default:
                self.target_course_id = self.default_target
                self.setup_source_step()
            else:
                query_name = self.query_one("#target_search_input", Input).value.strip()
                if not query_name:
                    error_label.update("Error: Please enter a target course name to search.")
                    return

                candidates = get_course_candidates_by_name(query_name, self.subdomain, self.api_key)
                if not candidates:
                    error_label.update("Error: No courses found matching that name.")
                    return

                select_widget = self.query_one("#target_select", Select)
                select_widget.set_options([(f"{c['name']} (ID: {c['id']})", str(c['id'])) for c in candidates])
                select_widget.remove_class("hidden-select")
                self.query_one("#target_search_input", Input).add_class("hidden-input")
                self.query_one("#target_choice_radios", RadioSet).add_class("hidden-widget")
                self.step = 1.5

        elif self.step == 1.5:
            select_widget = self.query_one("#target_select", Select)
            if select_widget.value is Select.BLANK or not select_widget.value:
                error_label.update("Error: Please select the correct target course.")
                return
            self.target_course_id = str(select_widget.value)
            select_widget.add_class("hidden-select")
            self.setup_source_step()

        elif self.step == 2:
            is_default = self.query_one("#source_default", RadioButton).value
            if is_default:
                self.source_course_id = self.default_source
                self.dismiss((self.target_course_id, self.source_course_id))
            else:
                query_name = self.query_one("#source_search_input", Input).value.strip()
                if not query_name:
                    error_label.update("Error: Please enter a source course name to search.")
                    return

                candidates = get_course_candidates_by_name(query_name, self.subdomain, self.api_key)
                if not candidates:
                    error_label.update("Error: No courses found matching that name.")
                    return

                select_widget = self.query_one("#source_select", Select)
                select_widget.set_options([(f"{c['name']} (ID: {c['id']})", str(c['id'])) for c in candidates])
                select_widget.remove_class("hidden-select")
                self.query_one("#source_search_input", Input).add_class("hidden-input")
                self.query_one("#source_choice_radios", RadioSet).add_class("hidden-widget")
                self.step = 2.5

        elif self.step == 2.5:
            select_widget = self.query_one("#source_select", Select)
            if select_widget.value is Select.BLANK or not select_widget.value:
                error_label.update("Error: Please select the correct source course.")
                return
            self.source_course_id = str(select_widget.value)
            self.dismiss((self.target_course_id, self.source_course_id))

    def setup_source_step(self) -> None:
        self.step = 2
        self.query_one("#step-label", Label).add_class("hidden-widget")
        self.query_one("#target_choice_radios", RadioSet).add_class("hidden-widget")
        self.query_one("#target_search_input", Input).add_class("hidden-input")

        self.query_one("#source-label", Label).remove_class("hidden-widget")
        self.query_one("#source_choice_radios", RadioSet).remove_class("hidden-widget")

    @on(Button.Pressed, "#cancel_btn")
    def handle_cancel(self) -> None:
        self.dismiss(None)

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
            try:
                new_course_id = course_reset()  # Uses defaults from .env
                subdomain = os.getenv("SUBDOMAIN")
                migration_url = f"https://{subdomain}.instructure.com/courses/{new_course_id}/content_migrations"
                # TODO Replace target_course_id with new_course_id
                self.notify(
                    f"Reset complete! [link={migration_url}]Click here to view migration status[/link]",
                    title="Success",
                    timeout=10
                )
            except (ValueError, RuntimeError) as e:
                self.notify(str(e), title="Course Reset Error", severity="error")
        elif event.button.id == "reset_other":
            def handle_custom_modal_dismiss(result):
                if not result:
                    return

                target_course_id, source_course_id = result
                try:
                    new_course_id = course_reset(target_course_id, source_course_id)
                    subdomain = os.getenv("SUBDOMAIN")
                    migration_url = f"https://{subdomain}.instructure.com/courses/{new_course_id}/content_migrations"
                    self.notify(
                        f"Reset complete! [link={migration_url}]Click here to view migration status[/link]",
                        title="Success",
                        timeout=10
                    )
                except (ValueError, RuntimeError) as e:
                    self.notify(str(e), title="Course Reset Error", severity="error")

            self.push_screen(CustomResetModal(), handle_custom_modal_dismiss)


if __name__ == "__main__":
    app = MainApp()
    app.run()
