import os
from dotenv import load_dotenv, set_key
from pathlib import Path
from urllib.parse import urlparse

from textual import on
from textual.app import ComposeResult

from textual.containers import Horizontal
from textual.widgets import Label, Button, Input, Link
from textual.screen import ModalScreen

env_path = Path(".env")

if not env_path.exists():
    env_path.touch()
    print("Created a new .env file for your configuration information.")

load_dotenv(dotenv_path=env_path)

class ConfigModal(ModalScreen):
    def compose(self) -> ComposeResult:
        subdomain = os.getenv("SUBDOMAIN", "")
        api_key = os.getenv("API_KEY", "")
        target_id = os.getenv("TARGET_COURSE_ID", "")
        source_id = os.getenv("SOURCE_COURSE_ID", "")

        yield Label("Configuration Settings", id="modal-title")

        # Subdomain section
        yield Label("Subdomain (e.g., 'yourschool' from yourschool.instructure.com):")
        yield Input(value=subdomain, id="SUBDOMAIN", placeholder="Enter subdomain...")

        # API Key section
        yield Label("Access Token:")
        yield Link("Click here for instructions", url="https://www.iorad.com/player/2053777/Canvas---How-to-generate-an-access-token#trysteps-1")
        with Horizontal(id="token_row"):
            yield Input(value=api_key, id="API_KEY", placeholder="Enter Access Token...", password=True)
            yield Button("🔑", id="toggle_token_visibility")

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

    @on(Button.Pressed, "#toggle_token_visibility")
    def toggle_token_visibility(self) -> None:
        token_input = self.query_one("#API_KEY", Input)
        token_input.password = not token_input.password

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
