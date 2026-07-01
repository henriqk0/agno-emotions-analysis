import reflex as rx
from chat.state import State
from chat.pages.input_section import input_section
from chat.pages.results_section import results_section
from chat.pages.processing_timeline import processing_timeline


def analysis_page() -> rx.Component:
    return rx.match(
        State.processing_stage,
        ("idle", input_section()),
        ("processing", processing_timeline()),
        ("complete", results_section()),
    )
