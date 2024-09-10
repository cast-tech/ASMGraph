# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

from src.ui.keywords import Events
from gi.repository import Gtk


class MultiWindow(Gtk.Window):
    open_windows = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MultiWindow.open_windows += 1
        self.connect(Events.DESTROY, self.on_destroy)

        self.show_all()

    def on_destroy(self, widget: Gtk.Widget) -> None:
        MultiWindow.open_windows -= 1
        if MultiWindow.open_windows == 0:
            Gtk.main_quit()
