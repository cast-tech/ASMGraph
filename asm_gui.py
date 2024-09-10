#!/usr/bin/env python3

# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import gi

gi.require_version("Gtk", "3.0")
gi.require_version('WebKit2', '4.0')

import json
import threading
from typing import Dict, Union
import shutil
import concurrent.futures

from src.ui.multi_window import MultiWindow
from src.ui.graph_visualizer import DotVisualizerWindow
from src.ui.command_builder import CommandBuilder
from src.ui.keywords import *
from src.ui.style_manager import StyleManager
from src.ui.error_handler import ErrorWindow
from src.ui.view_boxes import NewProject
from src.ui.help_window import HelpWindow
from src.ui.constants import *

from gi.repository import Gtk, GLib, GdkPixbuf


class ASMGWindow(MultiWindow):
    class Pages(str, Enum):
        MAIN = "main"
        NEW_PROJ = "new_project"

    def __init__(self) -> None:
        super().__init__(title=WINDOW_BASE_TITLE,
                         width_request=MAIN_WINDOW_WIDTH,
                         height_request=MAIN_WINDOW_HEIGHT)

        self.project_created = threading.Event()
        self.project_created.clear()
        self.retcode_of_execution: int = 0

        self.new_proj_box = None
        self.main_view = None
        self.search_proj_entry = None
        self.recent_projects = []
        self.progressbar = None

        self.stack = Gtk.Stack(transition_duration=DEFAULT_TRANSITION_DURATION,
                               transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.add(self.stack)

        self.command_builder = CommandBuilder()

    def handle_project_creation(self, project_type: ProjectType, out_dir: str) -> bool:
        if self.project_created.is_set():
            if self.retcode_of_execution == 0:
                self.open_graph_visualizer_window(out_dir, project_type)
                return False

            ErrorWindow(f"Execution failed with exit code: {self.retcode_of_execution}")
            self.project_created.clear()
        return True

    def setup_main_view(self) -> None:
        self.main_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        hbox = Gtk.HBox(border_width=20)
        self.main_view.add(hbox)
        self.main_view.add(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        logo = GdkPixbuf.Pixbuf.new_from_file('./images/asm-high.png')
        width = 100
        height = 26
        logo = logo.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
        logo_image = Gtk.Image.new_from_pixbuf(logo)
        logo_image.get_style_context().add_class("logo")
        hbox.pack_start(logo_image, False, False, 0)

        self.search_proj_entry = Gtk.SearchEntry(placeholder_text="Search projects")
        hbox.pack_start(self.search_proj_entry, True, True, 0)

        new_proj_button = Gtk.Button(label="New Project")
        new_proj_button.connect(Events.CLICKED, self.open_new_project)
        new_proj_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_1)
        hbox.pack_start(new_proj_button, False, True, 0)

        open_proj_button = Gtk.Button(label="Visualize Graphs")
        open_proj_button.connect(Events.CLICKED, self.visualize_project, ProjectType.BASIC)
        open_proj_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_1)
        hbox.pack_start(open_proj_button, False, True, 0)

        help_button = Gtk.Button(label="?")
        help_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_1)
        help_button.connect(Events.CLICKED, lambda _: HelpWindow().show_all())
        hbox.pack_start(help_button, False, True, 0)

        self.stack.add_named(self.main_view, self.Pages.MAIN)

    def setup_recent_projects_view(self) -> None:
        scrolled_window = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.main_view.pack_start(scrolled_window, True, True, 0)

        recent_proj_box = Gtk.VBox()
        self.search_proj_entry.connect(Events.CHANGED, self.search_project, recent_proj_box)

        def open_project(widget: Gtk.Button, project_dir: str, project_type: ProjectType) -> None:
            self.open_graph_visualizer_window(project_dir, project_type)

        def delete_project(widget: Gtk.Button, project_dir: str) -> None:
            dialog = Gtk.MessageDialog(
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="Confirm",
            )
            dialog.format_secondary_text(f"Are you sure you want to delete "
                                         f"the project at {project_dir}?")
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                shutil.rmtree(project_dir, ignore_errors=True)

                self.recent_projects = [proj for proj in self.recent_projects if
                                        proj[JSONKeywords.FOLDER_PATH] != project_dir]

                self.main_view.remove(scrolled_window)
                self.save_recent_projects()
                self.setup_recent_projects_view()
                self.show_all()

            dialog.destroy()

        for proj in self.recent_projects[::-1]:
            if proj[JSONKeywords.PROJECT_TYPE] == ProjectType.SPEC:
                label_text: str = f"{proj[JSONKeywords.PROJECT_NAME]} (SPEC)\n{proj[JSONKeywords.FOLDER_PATH]}"
            elif proj[JSONKeywords.PROJECT_TYPE] == ProjectType.SPEC_TUNE:
                label_text: str = f"{proj[JSONKeywords.PROJECT_NAME]} (SPEC_TUNE)\n{proj[JSONKeywords.FOLDER_PATH]}"
            else:
                label_text: str = f"{proj[JSONKeywords.PROJECT_NAME]}\n{proj[JSONKeywords.FOLDER_PATH]}"

            button_label = Gtk.Label(label=label_text, halign=Gtk.Align.START)
            button = Gtk.Button()
            button.get_style_context().add_class(CSSClasses.PROJECT_NAME)
            button.add(button_label)
            button.connect(Events.CLICKED, open_project, proj[JSONKeywords.FOLDER_PATH],
                           proj[JSONKeywords.PROJECT_TYPE])

            delete_button = Gtk.Button(label="x")
            delete_button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_2)
            delete_button.connect(Events.CLICKED, delete_project, proj[JSONKeywords.FOLDER_PATH])

            hbox = Gtk.HBox()
            hbox.pack_start(button, True, True, 0)
            hbox.pack_end(delete_button, False, False, 0)

            recent_proj_box.pack_start(hbox, False, True, 0)
            recent_proj_box.get_style_context().add_class(CSSClasses.DOT_FILES)


        scrolled_window.add(recent_proj_box)

    def setup_new_project_view(self) -> None:
        new_proj_view = Gtk.VBox()
        self.new_proj_box = NewProject()
        self.new_proj_box.connect(Events.CREATE, self.create_new_project)
        self.new_proj_box.connect(Events.CANCEL, self.cancel_project)

        new_proj_view.pack_start(self.new_proj_box, True, True, 0)

        self.progressbar = Gtk.ProgressBar(hexpand_set=True)
        new_proj_view.pack_end(self.progressbar, False, False, 0)

        self.new_proj_box.set_vexpand(True)
        self.new_proj_box.set_hexpand(True)

        self.stack.add_named(new_proj_view, self.Pages.NEW_PROJ)

        footer = self.new_proj_box.create_footer()
        new_proj_view.pack_end(footer, False, True, 0)

    def search_project(self, entry: Gtk.SearchEntry, recent_project_box: Gtk.Box) -> None:
        search_text: str = entry.get_text().lower()

        for project_box in recent_project_box.get_children():
            # Getting project name
            button_label: str = project_box.get_child().get_text().split("\n")[0].lower()
            if search_text in button_label:
                project_box.show()
            else:
                project_box.hide()

    def open_new_project(self, button: Gtk.Button) -> None:
        self.stack.set_visible_child_name(self.Pages.NEW_PROJ)

    def cancel_project(self, button: Gtk.Button) -> None:
        self.stack.set_visible_child_name(self.Pages.MAIN)

    def progress_update(self) -> bool:
        if self.project_created.is_set():
            self.progressbar.set_fraction(0)
            return False

        self.progressbar.pulse()
        return True

    def process_spec_project(self, values: Dict[str, Union[str, bool]]) -> int:
        command = self.command_builder.make_spec_collect_bbe_command(values)
        try:
            return_code: int = self.command_builder.execute(command)
            if return_code != 0:
                return return_code
        except Exception as e:
            ErrorWindow(f"While processing spec dir: {e}")
            return -1

        commands = self.command_builder.make_spec_visualize_commands(values[ViewsLabels.LOCATION],
                                                                     values[ViewsLabels.DISAS_PATH])

        num_workers = min(len(commands.keys()), 6)
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(self.command_builder.execute, command): exe_file
                for exe_file, command in commands.items()
            }

            for future in concurrent.futures.as_completed(futures):
                if future.result() != 0:
                    ErrorWindow(f"Failed {futures[future]}")

        return return_code

    def build_project(self, values: Dict[str, Union[str, bool]], project_type: str) -> None:

        if project_type == ProjectType.SPEC or project_type == ProjectType.SPEC_TUNE:
            return_code: int = self.process_spec_project(values)
        else:
            command = self.command_builder.make_visualize_command(values)
            try:
                return_code: int = self.command_builder.execute(command)
            except Exception as e:
                ErrorWindow(f"While creating dot files: {e}")
                return_code = -1

        if return_code == 0:
            proj_name: str = os.path.basename(values[ViewsLabels.LOCATION])
            project_data: Dict[str, str] = {
                JSONKeywords.PROJECT_NAME: proj_name,
                JSONKeywords.FOLDER_PATH: values[ViewsLabels.LOCATION],
                JSONKeywords.PROJECT_TYPE: project_type,
            }
            self.recent_projects.append(project_data)
            self.save_recent_projects()

        else:
            if os.path.isdir(values[ViewsLabels.LOCATION]):
                ErrorWindow("Failed project creation.")
                # The project could not be created. Cleaning up resources
                shutil.rmtree(values[ViewsLabels.LOCATION])

        self.retcode_of_execution = return_code
        self.project_created.set()

    def create_new_project(self, button: Gtk.Button) -> None:
        project_type = self.new_proj_box.get_current_view_name()

        active_view = self.new_proj_box.get_active_view(project_type)
        input_vals = active_view.validate_and_get_input_values()

        if not input_vals:
            return

        if input_vals.get(ViewsLabels.TUNE):
            project_type = ProjectType.SPEC_TUNE

        self.progressbar.set_fraction(0.0)
        GLib.timeout_add(100, self.progress_update)

        # TODO: freeze main window while execution
        threading.Thread(target=lambda: self.build_project(input_vals, project_type), daemon=True).start()
        GLib.timeout_add(3000, lambda: self.handle_project_creation(project_type, input_vals[ViewsLabels.LOCATION]))


    def project_exist(self, folder_path: str) -> bool:
        for proj in self.recent_projects:
            if proj[JSONKeywords.FOLDER_PATH] == folder_path:
                return True
        return False


    def open_and_save_project(self, folder_path: str, project_name: str, project_type: ProjectType) -> None:
        if not self.project_exist(folder_path):
            project_data: Dict[str, str] = {
                JSONKeywords.PROJECT_NAME: project_name,
                JSONKeywords.FOLDER_PATH: folder_path,
                JSONKeywords.PROJECT_TYPE: project_type
            }
            self.recent_projects.append(project_data)
            self.save_recent_projects()

        self.open_graph_visualizer_window(folder_path, project_type)


    def visualize_project(self, button: Gtk.Button, project_type: ProjectType) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Please choose a folder",
            parent=None,
            action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        response: int = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_folder: str = dialog.get_filename()
            # Set the base name of the folder path as the project name
            self.open_and_save_project(selected_folder, os.path.basename(selected_folder), project_type)

        dialog.destroy()

    def load_recent_projects(self) -> None:
        with open(RECENT_PROJECTS_FILE, 'r') as file:
            self.recent_projects = json.load(file)

    def save_recent_projects(self) -> None:
        with open(RECENT_PROJECTS_FILE, 'w') as file:
            json.dump(self.recent_projects, file)

    @staticmethod
    def set_default_work_dir() -> None:
        if not os.path.exists(DEFAULT_WORK_DIR):
            os.makedirs(DEFAULT_WORK_DIR)

    def set_recent_projects(self) -> None:
        if not os.path.exists(RECENT_PROJECTS_FILE):
            self.save_recent_projects()
        else:
            self.load_recent_projects()

    def setup_workplace(self) -> None:
        self.set_default_work_dir()
        self.set_recent_projects()


    def open_graph_visualizer_window(self, project_dir: str, project_type: ProjectType) -> None:
        DotVisualizerWindow(project_dir, project_type)
        self.destroy()


def main() -> None:
    StyleManager().apply_styles()

    win = ASMGWindow()
    win.setup_workplace()
    win.setup_main_view()
    win.setup_recent_projects_view()
    win.setup_new_project_view()
    win.show_all()

    Gtk.main()


if __name__ == '__main__':
    main()
