import reflex as rx
from chat.state import State


def step_icon(step: dict) -> rx.Component:
    return rx.match(
        step.get("step_type"),
        ("tool_call", rx.match(
            step.get("status"),
            ("running", rx.icon("loader-circle", size=18, color=rx.color("accent", 9))),
            ("done", rx.icon("check-circle", size=18, color=rx.color("green", 9))),
            rx.icon("circle", size=18, color=rx.color("mauve", 7)),
        )),
        ("reasoning", rx.icon("sparkles", size=18, color=rx.color("yellow", 9))),
        rx.icon("circle", size=18, color=rx.color("mauve", 7)),
    )


def step_card(step: dict) -> rx.Component:
    return rx.hstack(
        step_icon(step),
        rx.text(step.get("label", ""), size="2"),
        spacing="3",
        align_items="center",
        padding="8px 12px",
        width="100%",
    )


def processing_timeline() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="2"),
            rx.heading("Analisando...", size="5"),
            rx.text("Acompanhe o processo em tempo real.", size="2", color=rx.color("mauve", 10)),
            rx.cond(
                State.steps,
                rx.vstack(
                    rx.divider(),
                    rx.foreach(State.steps, step_card),
                    spacing="1",
                    width="100%",
                ),
            ),
            spacing="4",
            align_items="center",
            max_width="600px",
            width="100%",
            padding="32px 16px",
        ),
        flex="1",
        padding="16px",
    )
