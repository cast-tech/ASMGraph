# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import os
from typing import Optional

from src.ui.keywords import CSSClasses, Events
from src.ui.error_handler import ErrorWindow

from gi.repository import Gtk, GObject


class ActionBox(Gtk.HBox):
    def __init__(self, label: str) -> None:
        super().__init__()

        self.label_text = label

        self.label_widget = Gtk.Label(label=self.label_text)
        spacer_label = Gtk.Label(width_request=20,
                                 height_request=1)
        self.label_widget.set_width_chars(25)
        self.label_widget.set_alignment(0, 0.7)

        self.pack_start(self.label_widget, False, True, 0)
        self.pack_start(spacer_label, False, False, 0)

        self.entry: Optional[Gtk.Entry] = None

    def select_path(self, button: Gtk.Button, action: Gtk.FileChooserAction) -> None:
        title = "Please select a "
        if action == Gtk.FileChooserAction.SELECT_FOLDER:
            title += "folder"
        else:
            title += "file"

        dialog = Gtk.FileChooserDialog(title=title, parent=None, action=action)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        response: int = dialog.run()

        if response == Gtk.ResponseType.OK:
            selected_path: str = dialog.get_filename()
            self.entry.set_text(selected_path)

        dialog.destroy()

    def notify_error(self) -> None:
        context_style = self.label_widget.get_style_context()
        context_style.remove_class(CSSClasses.LABEL_DEFAULT)
        context_style.add_class(CSSClasses.LABEL_ERROR)

    def set_default_color(self) -> None:
        context_style = self.label_widget.get_style_context()
        context_style.remove_class(CSSClasses.LABEL_ERROR)
        context_style.add_class(CSSClasses.LABEL_DEFAULT)

    def set_hint(self, text):
        self.label_widget.set_tooltip_text(text)

# TODO: add filter for files selection
class FileSelectorBox(ActionBox):
    def __init__(self, label: str) -> None:
        super().__init__(label)
        self.entry = Gtk.Entry()
        browse_button = Gtk.Button(label="...")
        browse_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_1)
        browse_button.connect(Events.CLICKED, self.select_path, Gtk.FileChooserAction.OPEN)

        self.pack_start(self.entry, True, True, 0)
        self.pack_end(browse_button, False, True, 0)

    def has_valid_input(self) -> bool:
        self.set_default_color()
        value: str = self.get_text()
        if not os.path.isfile(value):
            if len(value) > 0:
                ErrorWindow(f"No such file: '{value}'")
            self.notify_error()
            return False
        return True

    def set_text(self, text: str) -> None:
        self.entry.set_text(text)

    def get_text(self) -> str:
        return self.entry.get_text().strip()


class FolderSelectorBox(ActionBox):
    def __init__(self, label: str) -> None:
        super().__init__(label)
        self.entry = Gtk.Entry()
        browse_button = Gtk.Button(label="...")
        browse_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_1)
        browse_button.connect(Events.CLICKED, self.select_path,
                              Gtk.FileChooserAction.SELECT_FOLDER)

        self.pack_start(self.entry, True, True, 0)
        self.pack_end(browse_button, False, True, 0)

    def has_valid_input(self) -> bool:
        self.set_default_color()
        value: str = self.get_text()
        if not os.path.isdir(value):
            if len(value) > 0:
                ErrorWindow(f"No such directory: {value}")
            self.notify_error()
            return False
        return True

    def set_text(self, text: str) -> None:
        self.entry.set_text(text)

    def get_text(self) -> str:
        return self.entry.get_text().strip()


class SwitchBox(ActionBox):
    def __init__(self, label: str) -> None:
        super().__init__(label)
        self.switch = Gtk.Switch(active=False)
        self.pack_start(self.switch, False, True, 0)

    def set_active(self, value: bool) -> None:
        self.switch.set_active(value)

    def get_active(self) -> bool:
        return self.switch.get_active()


class CheckBox(ActionBox):
    __gsignals__ = {
        Events.TOGGLED: (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, label: str) -> None:
        super().__init__(label)
        self.check = Gtk.CheckButton(active=False)
        self.pack_start(self.check, False, True, 0)

        self.check.connect(Events.TOGGLED, lambda _: self.emit(Events.TOGGLED))

    def set_active(self, value: bool) -> None:
        self.check.set_active(value)

    def get_active(self) -> bool:
        return self.check.get_active()


class TextBox(ActionBox):
    def __init__(self, label: str) -> None:
        super().__init__(label)
        self.entry = Gtk.Entry()
        self.pack_start(self.entry, True, True, 0)

    def set_text(self, text: str) -> None:
        self.entry.set_text(text)

    def set_placeholder_text(self, text: str) -> None:
        self.entry.set_placeholder_text(text)

    def get_text(self) -> str:
        return self.entry.get_text().strip()
