# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

from src.ui.keywords import Events
from src.ui.constants import ERROR_WINDOW_WIDTH, ERROR_WINDOW_HEIGHT

from gi.repository import Gtk


class ErrorWindow(Gtk.Window):
    def __init__(self, error_message: str) -> None:
        super().__init__(title="Error",
                         default_width=ERROR_WINDOW_WIDTH,
                         default_height=ERROR_WINDOW_HEIGHT,
                         window_position=Gtk.WindowPosition.CENTER)

        label = Gtk.Label(label="Error: " + error_message)

        close_button = Gtk.Button(label="Close")
        close_button.connect(Events.CLICKED, self.close)

        vbox = Gtk.VBox(spacing=10)
        vbox.pack_start(label, True, True, 5)
        vbox.pack_start(close_button, False, False, 0)

        self.add(vbox)
        # Set the minimum size of the window based on the length of the error message
        label_width: int
        label_height: int
        label_width, label_height = label.get_layout().get_pixel_size()
        self.set_size_request(label_width + 20, label_height + 60)

        self.show_all()

    def close(self, button: Gtk.Button) -> None:
        self.destroy()
