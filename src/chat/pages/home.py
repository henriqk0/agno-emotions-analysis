import reflex as rx
from chat.state import State


def feature_card(feature: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon(feature["icon"], size=36, color=rx.color("accent", 9)),
            rx.heading(feature["title"], size="4", text_align="center"),
            rx.text(
                feature["description"],
                text_align="center",
                color=rx.color("mauve", 11),
                size="2",
            ),
            rx.button(
                "Começar",
                on_click=lambda: State.select_feature(feature["id"]),
                margin_top="8px",
            ),
            spacing="3",
            align_items="center",
            padding="24px",
        ),
        width="100%",
        max_width="400px",
    )


def home_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.vstack(
                rx.heading("Análise de Emoções no YouTube", size="7", text_align="center"),
                rx.text(
                    "Descubra como a audiência reage aos vídeos mais populares sobre qualquer tema.",
                    text_align="center",
                    color=rx.color("mauve", 11),
                    size="4",
                ),
                spacing="3",
                width="100%",
                max_width="600px",
                align_items="center",
            ),
            rx.divider(width="100%", max_width="600px"),
            rx.heading("Ferramentas disponíveis", size="5"),
            rx.flex(
                rx.foreach(State.features, feature_card),
                flex_wrap="wrap",
                justify="center",
                gap="16px",
                width="100%",
            ),
            spacing="6",
            padding="40px 16px",
            align_items="center",
            width="100%",
            max_width="900px"
        ),
        flex="1",
        padding="16px",
    )
