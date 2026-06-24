import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import reflex as rx

config = rx.Config(
    app_name="chat",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="dark",
                accent_color="purple",
            ),
        ),
    ],
)