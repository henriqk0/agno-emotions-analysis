import reflex as rx

from chat.components import navbar
from chat.pages.home import home_page
from chat.pages.analysis import analysis_page
from chat.state import State


def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.match(
            State.current_page,
            ("home", home_page()),
            ("analysis", analysis_page()),
        ),
        background_color=rx.color("mauve", 1),
        color=rx.color("mauve", 12),
        height="100dvh",
        align_items="stretch",
        spacing="0",
    )


app = rx.App()
app.add_page(index)
