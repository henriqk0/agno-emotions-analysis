import reflex as rx
from chat.state import State


def navbar():
    return rx.hstack(
        rx.hstack(
            rx.icon("sparkles", size=20, color=rx.color("accent", 9)),
            rx.heading("Emoções Analysis", size="4"),
            spacing="2",
            align_items="center",
            on_click=State.go_home,
            cursor="pointer",
        ),
        rx.hstack(
            rx.cond(
                State.current_page == "analysis",
                rx.button(
                    rx.icon("home", size=16),
                    "Início",
                    variant="ghost",
                    size="2",
                    on_click=State.go_home,
                ),
            ),
            rx.select(
                State.model_list,
                value=State.current_model,
                on_change=State.set_model,
                placeholder="Modelo",
                size="2",
                variant="soft",
            ),
            spacing="3",
            align_items="center",
        ),
        justify_content="space-between",
        align_items="center",
        padding="12px 16px",
        border_bottom=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
    )
