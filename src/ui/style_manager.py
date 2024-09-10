# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import os

from src.ui.constants import GTK_STYLE_PROVIDER_PRIORITY_APPLICATION, UI_DIR, STYLE_CSS
from gi.repository import Gtk, Gdk


class StyleManager:
    def __init__(self) -> None:
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_path(os.path.join(UI_DIR, STYLE_CSS))

    def apply_styles(self) -> None:
        display = Gdk.Display()
        screen = Gdk.Display.get_default_screen(display.get_default())
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen=screen,
                                              provider=self.css_provider,
                                              priority=GTK_STYLE_PROVIDER_PRIORITY_APPLICATION)

        settings = Gtk.Settings()
        default_settings = settings.get_default()
        default_settings.props.gtk_application_prefer_dark_theme = True
