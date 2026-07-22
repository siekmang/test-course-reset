import os

from textual import on
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Select, RadioSet, RadioButton
from textual.screen import ModalScreen

from src.screens.confirm_modal import ConfirmModal
from src.services.get_course_candidates import get_course_candidates_by_name

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
        yield Input(placeholder="Enter target course name or ID...", id="target_search_input", classes="hidden-input")
        yield Select([], id="target_select", prompt="Select correct target course", classes="hidden-select")

        yield Label(f"Source Course: Use default ({self.default_source}) or search a different one?", id="source-label", classes="hidden-widget")
        yield RadioSet(
            RadioButton("Use Default Source Course", id="source_default", value=True),
            RadioButton("Search for a Different Course", id="source_search"),
            id="source_choice_radios",
            classes="hidden-widget"
        )
        yield Input(placeholder="Enter source course name or ID...", id="source_search_input", classes="hidden-input")
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

        def _is_course_id(value: str) -> bool:
            return value.isdigit()

        if self.step == 1:
            is_default = self.query_one("#target_default", RadioButton).value
            if is_default:
                self.target_course_id = self.default_target
                self.setup_source_step()
            else:
                query_name = self.query_one("#target_search_input", Input).value.strip()
                if not query_name:
                    error_label.update("Error: Please enter a target course name or ID.")
                    return

                if _is_course_id(query_name):
                    def handle_id_confirm(confirmed: bool | None) -> None:
                        if confirmed:
                            self.target_course_id = query_name
                            self.setup_source_step()
                    self.app.push_screen(
                        ConfirmModal(message=f"Use course ID {query_name} as the target?"),
                        handle_id_confirm,
                    )
                    return

                candidates = get_course_candidates_by_name(query_name, self.subdomain, self.api_key)
                if not candidates:
                    error_label.update("Error: No courses found matching that name.")
                    return

                self.target_candidates = {str(c["id"]): c["name"] for c in candidates}
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
            course_name = self.target_candidates.get(self.target_course_id, "")

            if "test" not in course_name.lower():
                def handle_test_confirm(confirmed: bool | None) -> None:
                    if confirmed:
                        select_widget.add_class("hidden-select")
                        self.setup_source_step()
                self.app.push_screen(
                    ConfirmModal(
                        message=f'"{course_name}" doesn\'t look like a test course. Reset it anyway?'
                    ),
                    handle_test_confirm,
                )
                return

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
                    error_label.update("Error: Please enter a source course name or ID.")
                    return

                if _is_course_id(query_name):
                    def handle_id_confirm(confirmed: bool | None) -> None:
                        if confirmed:
                            self.target_course_id = query_name
                            self.setup_source_step()
                    self.app.push_screen(
                        ConfirmModal(message=f"Use course ID {query_name} as the target?"),
                        handle_id_confirm,
                    )
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

            def handle_confirm(confirmed: bool | None) -> None:
                if confirmed:
                    self.dismiss((self.target_course_id, self.source_course_id))
            self.app.push_screen(
                ConfirmModal(message=f"Use course ID {self.source_course_id} as the source? This will overwrite the target course."),
                handle_confirm,
            )

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
