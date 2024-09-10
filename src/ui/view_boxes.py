# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import os.path

from abc import abstractmethod
from glob import glob
from typing import Optional, Union, Dict, Tuple, Type

from src.ui.action_boxes import TextBox, FolderSelectorBox, FileSelectorBox, CheckBox
from src.ui.constants import *
from src.ui.error_handler import ErrorWindow
from src.ui.keywords import *

from gi.repository import Gtk, GObject, GLib


class BaseViewBox(Gtk.Box):
    __gsignals__ = {
        Events.CREATE: (GObject.SignalFlags.RUN_FIRST, None, ()),
        Events.CANCEL: (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    @staticmethod
    def get_project_default_values() -> Tuple[str, str]:
        existing_dir_numbers = set()

        for d in glob(os.path.join(DEFAULT_WORK_DIR, BASE_WORK_DIR_NAME + "*")):
            if os.path.isdir(os.path.join(DEFAULT_WORK_DIR, d)):
                try:
                    base_name: str = os.path.basename(d)
                    number: int = int(base_name[len(BASE_WORK_DIR_NAME):])
                    existing_dir_numbers.add(number)
                except ValueError:
                    pass  # Ignore directories that don't match the expected pattern

        next_number: int = 1
        while next_number in existing_dir_numbers:
            next_number += 1
        return (BASE_WORK_DIR_NAME + str(next_number),
                os.path.join(DEFAULT_WORK_DIR, BASE_WORK_DIR_NAME + str(next_number)))

    @abstractmethod
    def validate_and_get_input_values(self) -> Optional[Dict[str, Union[str, bool]]]:
        raise NotImplementedError("Subclasses must implement this method.")

    def trigger_create_signal(self, button: Gtk.Button) -> None:
        self.emit(Events.CREATE)

    def trigger_cancel_signal(self, button: Gtk.Button) -> None:
        self.emit(Events.CANCEL)


# TODO: Perhaps, we need an option to specialize the function names
class VisualizeViewBox(BaseViewBox):
    class BoxTypes(str, Enum):
        BIN = "bin_box"
        ASM = "asm_box"

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.get_style_context().add_class(CSSClasses.CONTENT_BOX)
        self.get_style_context().add_class(CSSClasses.VIS_BOX)

        name, directory = self.get_project_default_values()

        self.project_name = TextBox(ViewsLabels.PROJECT_NAME)
        self.project_name.set_text(name)
        self.pack_start(self.project_name, False, False, 0)

        self.project_dir = FolderSelectorBox(ViewsLabels.LOCATION)
        self.project_dir.set_text(directory)
        self.pack_start(self.project_dir, False, False, 0)

        radio_button_box = Gtk.HBox()
        radio_button_box.get_style_context().add_class(CSSClasses.RADIOBUTTON_BOX)
        radio_button_bin = Gtk.RadioButton.new_with_label_from_widget(None,
                                                                      ViewsLabels.BIN_RADIO)
        radio_button_bin.connect(Events.TOGGLED, self.make_visible, self.BoxTypes.BIN)

        radio_button_asm = Gtk.RadioButton.new_with_label_from_widget(radio_button_bin,
                                                                      ViewsLabels.ASM_RADIO)
        radio_button_asm.connect(Events.TOGGLED, self.make_visible, self.BoxTypes.ASM)
        radio_button_box.pack_start(radio_button_bin, False, False, 0)
        radio_button_box.pack_start(radio_button_asm, False, False, 0)

        self.asm_box = Gtk.VBox()
        GLib.idle_add(self.asm_box.hide)
        self.bin_box = Gtk.VBox()
        self.common_box = Gtk.VBox()

        self.disas_path = FileSelectorBox(ViewsLabels.DISAS_PATH)
        self.bin_box.pack_start(self.disas_path, False, False, 0)
        self.bin_path = FileSelectorBox(ViewsLabels.BIN_PATH)
        self.bin_box.pack_start(self.bin_path, False, False, 0)

        self.asm_path = FileSelectorBox(ViewsLabels.ASM_PATH)
        self.asm_box.pack_start(self.asm_path, False, False, 0)

        self.bbexec_path = FileSelectorBox(ViewsLabels.BBEXEC_PATH)
        self.singleton = CheckBox(ViewsLabels.SINGLETON)
        self.singleton.set_hint("Highlight singleton basic blocks.")

        self.bbexec_path.get_style_context().add_class(CSSClasses.INNER_BOX_BIN)
        self.singleton.get_style_context().add_class(CSSClasses.INNER_BOX_BIN)

        self.common_box.pack_start(self.bbexec_path, False, False, 0)
        self.common_box.pack_start(self.singleton, False, False, 0)

        self.pack_start(radio_button_box, False, False, 0)
        self.pack_start(self.bin_box, False, False, 0)
        self.pack_start(self.asm_box, False, False, 0)
        self.pack_start(self.common_box, False, False, 0)

    def validate_and_get_input_values(self) -> Optional[Dict[str, Union[str, bool]]]:
        found_input_error: bool = False
        values: Dict[str, Union[str, bool]] = {}

        input_value: str = self.project_dir.get_text()
        if os.path.exists(input_value):
            ErrorWindow(f"There is already such a directory:{input_value}")
            self.project_dir.notify_error()
            found_input_error = True
        elif not input_value:
            self.project_dir.notify_error()
            found_input_error = True
        else:
            self.project_dir.set_default_color()
            values[ViewsLabels.LOCATION] = input_value

        if self.bin_box.get_visible():
            if self.bin_path.has_valid_input():
                values[ViewsLabels.BIN_PATH] = self.bin_path.get_text()
            else:
                found_input_error = True

            if self.disas_path.has_valid_input():
                values[ViewsLabels.DISAS_PATH] = self.disas_path.get_text()
            else:
                found_input_error = True

        else:
            if self.asm_path.has_valid_input():
                values[ViewsLabels.ASM_PATH] = self.asm_path.get_text()
            else:
                found_input_error = True

        input_value: str = self.bbexec_path.get_text()
        if input_value:
            if self.bbexec_path.has_valid_input():
                values[ViewsLabels.BBEXEC_PATH] = input_value
            else:
                found_input_error = True

        values[ViewsLabels.SINGLETON] = self.singleton.get_active()

        return values if not found_input_error else None

    def make_visible(self, button: Gtk.RadioButton, box_name: str) -> None:
        if box_name == self.BoxTypes.ASM:
            self.bin_box.hide()
            self.asm_box.show()
        elif box_name == self.BoxTypes.BIN:
            self.asm_box.hide()
            self.bin_box.show()


class SpecViewBox(BaseViewBox):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.get_style_context().add_class(CSSClasses.CONTENT_BOX)
        self.get_style_context().add_class(CSSClasses.SPEC_BOX)

        name, directory = self.get_project_default_values()

        self.project_name = TextBox(label=ViewsLabels.PROJECT_NAME)
        self.project_name.set_text(name)

        self.project_dir = FolderSelectorBox(ViewsLabels.LOCATION)
        self.project_dir.set_text(directory)

        self.spec_path = FolderSelectorBox(ViewsLabels.SPEC_PATH)

        self.objdump_path = FileSelectorBox(ViewsLabels.DISAS_PATH)

        self.base = CheckBox(ViewsLabels.BASE)
        self.pick = CheckBox(ViewsLabels.PICK)
        self.tune = CheckBox(ViewsLabels.TUNE)
        self.tune.connect(Events.TOGGLED, self.tune_toggled)

        self.base.get_style_context().add_class(CSSClasses.ACTION_BOX)
        self.pick.get_style_context().add_class(CSSClasses.ACTION_BOX)
        self.tune.get_style_context().add_class(CSSClasses.ACTION_BOX)

        self.disas_path = FileSelectorBox(ViewsLabels.DISAS_PATH)

        self.inner_box = Gtk.VBox()
        self.inner_box.pack_start(self.project_name, False, False, 0)
        self.inner_box.pack_start(self.project_dir, False, False, 0)
        self.inner_box.pack_start(self.spec_path, False, False, 0)
        self.inner_box.pack_start(self.base, False, False, 0)
        self.inner_box.pack_start(self.pick, False, False, 0)
        self.inner_box.pack_start(self.tune, False, False, 0)
        self.inner_box.pack_start(self.disas_path, False, False, 0)
        self.pack_start(self.inner_box, False, False, 0)

    def tune_toggled(self, checkbutton: CheckBox):
        self.base.set_active(checkbutton.get_active())
        self.pick.set_active(checkbutton.get_active())



    def validate_and_get_input_values(self) -> Optional[Dict[str, Union[str, bool]]]:
        found_input_error: bool = False
        values: Dict[str, Union[str, bool]] = {}

        input_value = self.project_dir.get_text()
        if os.path.exists(input_value):
            ErrorWindow(f"There is already such a directory:{input_value}")
            self.project_dir.notify_error()
            found_input_error = True
        elif not input_value:
            self.project_dir.notify_error()
            found_input_error = True
        else:
            self.project_dir.set_default_color()
            values[ViewsLabels.LOCATION] = input_value

        if not self.spec_path.has_valid_input():
            found_input_error = True
        else:
            values[ViewsLabels.SPEC_PATH] = self.spec_path.get_text()

        if not self.base.get_active() and not self.pick.get_active():
            self.base.notify_error()
            self.pick.notify_error()
            self.tune.notify_error()
            found_input_error = True
        else:
            self.base.set_default_color()
            self.pick.set_default_color()
            self.tune.set_default_color()
            values[ViewsLabels.BASE] = self.base.get_active()
            values[ViewsLabels.PICK] = self.pick.get_active()
            values[ViewsLabels.TUNE] = self.tune.get_active()

        if self.disas_path.has_valid_input():
            values[ViewsLabels.DISAS_PATH] = self.disas_path.get_text()
        else:
            found_input_error = True

        return values if not found_input_error else None


class NewProject(BaseViewBox):
    def __init__(self) -> None:
        super().__init__()
        scrolled_window_buttons = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER,
                                                     vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.pack_start(scrolled_window_buttons, False, True, 0)

        button_box = Gtk.VBox()
        scrolled_window_buttons.add(button_box)

        visualize_button_label = Gtk.Label(label=ViewsLabels.VISUALIZE,
                                           halign=Gtk.Align.START)
        visualize_button = Gtk.Button()
        visualize_button.add(visualize_button_label)
        visualize_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_2)

        spec_button_label = Gtk.Label(label=ViewsLabels.SPEC,
                                      halign=Gtk.Align.START)
        spec_button = Gtk.Button()
        spec_button.add(spec_button_label)
        spec_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_2)

        visualize_button.connect(Events.CLICKED, self.set_view, ProjectType.BASIC)
        spec_button.connect(Events.CLICKED, self.set_view, ProjectType.SPEC)

        button_box.pack_start(visualize_button, False, True, 0)
        button_box.pack_start(spec_button, False, True, 0)

        view_box = Gtk.VBox()
        self.pack_end(view_box, True, True, 0)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_UP_DOWN,
                               transition_duration=DEFAULT_TRANSITION_DURATION)
        view_box.pack_start(self.stack, True, True, 0)

        # To store the currently active view name
        self.current_view_name = None

        # To store values of active views
        self.view_values = {}

        self.create_view(ProjectType.BASIC, VisualizeViewBox)
        self.create_view(ProjectType.SPEC, SpecViewBox)

        # set visualize as default active view
        self.current_view_name = ProjectType.BASIC
        self.stack.set_visible_child_name(ProjectType.BASIC)

    def create_footer(self) -> Gtk.HBox:
        footer = Gtk.HBox()
        footer.get_style_context().add_class(CSSClasses.FOOTER)

        cancel_button = Gtk.Button(label=ViewsLabels.CANCEL)
        cancel_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_1)
        cancel_button.connect(Events.CLICKED, self.trigger_cancel_signal)

        create_button = Gtk.Button(label=ViewsLabels.CREATE)
        create_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_1)
        create_button.connect(Events.CLICKED, self.trigger_create_signal)

        footer.pack_end(cancel_button, False, False, 0)
        footer.pack_end(create_button, False, False, 0)

        return footer

    def create_view(self, view_type: str, view_box: Type[Gtk.Box]) -> None:
        view = view_box()
        view.connect(Events.CREATE, self.trigger_create_signal)
        view.connect(Events.CANCEL, self.trigger_cancel_signal)

        self.view_values[view_type] = view
        self.stack.add_named(view, view_type)

    def set_view(self, button: Gtk.Button, view_name: str) -> None:
        self.current_view_name = view_name
        self.stack.set_visible_child_name(view_name)

    def get_current_view_name(self) -> ProjectType:
        return self.current_view_name

    def get_active_view(self, view_name: str) -> BaseViewBox:
        return self.view_values[view_name]
