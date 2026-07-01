import reflex as rx
from chat.state import State

SUGGESTIONS = ["games", "technology", "music", "sports", "movies", "education"]


def suggestion_chip(topic: str) -> rx.Component:
    return rx.badge(
        topic,
        on_click=lambda: State.set_input(topic),
        variant="soft",
        color_scheme="purple",
        cursor="pointer",
        _hover={"opacity": 0.8},
    )


def error_card() -> rx.Component:
    return rx.cond(
        State.error,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("alert-triangle", size=20, color=rx.color("red", 9)),
                    rx.heading("Serviço indisponível", size="4", color=rx.color("red", 9)),
                    spacing="2",
                ),
                rx.text(State.error, size="2", color=rx.color("mauve", 11)),
                rx.button(
                    rx.icon("rotate-cw", size=16),
                    "Tentar Novamente",
                    on_click=State.reset_analysis,
                    variant="surface",
                    color_scheme="red",
                ),
                spacing="3",
                align_items="flex-start",
            ),
            width="100%",
        ),
    )


def input_section() -> rx.Component:
    return rx.center(
        rx.vstack(
            error_card(),
            rx.vstack(
                rx.icon("message-square-heart", size=40, color=rx.color("accent", 9)),
                rx.heading(
                    "Análise de Emoções em Comentários do YouTube",
                    size="6",
                    text_align="center",
                ),
                rx.text(
                    "Digite um tema para buscar os vídeos mais populares e analisar as emoções nos comentários.",
                    text_align="center",
                    color=rx.color("mauve", 11),
                    size="3",
                ),
                spacing="3",
                align_items="center",
            ),
            rx.divider(width="100%"),
            rx.form(
                rx.vstack(
                    rx.hstack(
                        rx.input(
                            value=State.user_input,
                            on_change=State.set_input,
                            placeholder="Ex: games, tecnologia, música brasileira...",
                            size="3",
                            flex="1",
                        ),
                        rx.button(
                            rx.icon("search", size=16),
                            "Analisar",
                            type="submit",
                            size="3",
                            loading=State.processing,
                            disabled=State.processing,
                        ),
                        width="100%",
                        spacing="2",
                    ),
                    rx.flex(
                        rx.foreach(SUGGESTIONS, suggestion_chip),
                        wrap="wrap",
                        gap="8px",
                        justify="center",
                    ),
                    spacing="3",
                    width="100%",
                ),
                on_submit=State.start_analysis,
                width="100%",
            ),
            spacing="6",
            max_width="600px",
            width="100%",
            padding="32px",
            align_items="stretch",
        ),
        flex="1",
        padding="16px",
    )
