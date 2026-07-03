import reflex as rx
from chat.state import State


def summary_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("file-text", size=20, color=rx.color("accent", 9)),
                rx.heading("Resumo da Análise", size="4"),
                spacing="2",
            ),
            rx.divider(),
            rx.markdown(State.result_summary),
            spacing="2",
            align_items="stretch",
        ),
        width="100%",
    )


def emotion_pie_chart() -> rx.Component:
    palette = ["#4f46e5", "#ec4899", "#10b981", "#f59e0b", "#3b82f6", "#8b5cf6"]
    pie_cells = [rx.recharts.cell(fill=color) for color in palette]

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("pie-chart", size=20, color=rx.color("accent", 9)),
                rx.heading("Distribuição Geral", size="4"),
                spacing="2",
            ),
            rx.divider(),
            rx.recharts.pie_chart(
                rx.recharts.pie(
                    data=State.distribution_data,
                    data_key="value",
                    name_key="name",
                    cx="50%",
                    cy="50%",
                    outer_radius="60%",
                    label=True,
                    stroke="#ffffff",
                    stroke_width=2,
                    *pie_cells,
                ),
                rx.recharts.legend(),
                width="100%",
                height=300,
            ),
            spacing="2",
            align_items="stretch",
        ),
        width="100%",
    )


def detailed_bar_chart() -> rx.Component:
    palette = ["#4f46e5", "#ec4899", "#10b981", "#f59e0b", "#3b82f6", "#8b5cf6"]
    bar_cells = [rx.recharts.cell(fill=color) for color in palette]

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bar-chart-3", size=20, color=rx.color("accent", 9)),
                rx.heading("Emoções Detalhadas", size="4"),
                spacing="2",
            ),
            rx.divider(),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    radius=[4, 4, 0, 0],
                    *bar_cells,
                ),
                rx.recharts.x_axis(
                    data_key="name",
                    tick={"fill": "white"}),
                rx.recharts.y_axis(),
                rx.recharts.tooltip(),
                data=State.detailed_emotion_data,
                width="100%",
                height=300,
            ),
            spacing="2",
            align_items="stretch",
        ),
        width="100%",
    )


def key_insights_list() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("lightbulb", size=20, color=rx.color("accent", 9)),
                rx.heading("Insights Principais", size="4"),
                spacing="2",
            ),
            rx.divider(),
            rx.foreach(
                State.result_key_insights,
                lambda insight: rx.hstack(
                    rx.icon("circle-check", size=16, color=rx.color("accent", 9)),
                    rx.text(insight, size="2"),
                    spacing="2",
                    align_items="center",
                ),
            ),
            spacing="2",
            align_items="stretch",
        ),
        width="100%",
    )


def comment_card(comment: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.box(
                rx.text(comment["text"], size="2", italic=True),
                flex="1",
            ),
            rx.badge(
                comment.get("emotion", ""),
                variant="soft",
                color_scheme="purple",
                size="1",
            ),
            spacing="3",
            align_items="flex-start",
            width="100%",
        ),
        width="100%",
    )


def top_comments_list() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("message-square", size=20, color=rx.color("accent", 9)),
                rx.heading("Comentários em Destaque", size="4"),
                spacing="2",
            ),
            rx.divider(),
            rx.foreach(State.result_top_comments, comment_card),
            spacing="2",
            align_items="stretch",
        ),
        width="100%",
    )


def action_buttons() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("rotate-cw", size=16),
            "Nova Análise",
            on_click=State.reset_analysis,
            variant="surface",
        ),
        rx.button(
            rx.icon("home", size=16),
            "Voltar ao Início",
            on_click=State.go_home,
            variant="ghost",
        ),
        spacing="3",
        justify="center",
        width="100%",
    )


def results_section() -> rx.Component:
    return rx.center(
        rx.vstack(
            summary_card(),
            rx.hstack(
                emotion_pie_chart(),
                detailed_bar_chart(),
                flex_wrap="wrap",
                width="100%",
                spacing="4",
            ),
            key_insights_list(),
            top_comments_list(),
            action_buttons(),
            spacing="6",
            max_width="900px",
            width="100%",
            padding="32px 16px",
            align_items="stretch",
        ),
        flex="1",
        padding="16px",
    )
