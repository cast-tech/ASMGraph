# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import os.path
import uuid
from cProfile import label
from glob import glob
from typing import List, Optional
import threading
import xdot

from src.ui.constants import *
from src.ui.keywords import CSSClasses, Events, ViewsLabels, DotFileVisualizerOrientations, ProjectType
from src.ui.help_window import HelpWindow
from src.ui.multi_window import MultiWindow
from src.ui.plugins_manager import PluginsManager
from src.ui.error_handler import ErrorWindow
from src.ui.action_boxes import FileSelectorBox, CheckBox
from src.ui.command_builder import CommandBuilder
from src.bbe_parser import BBEFileParser, TOTAL_DYN_INST
from gi.repository import GObject, Gtk, GLib


def human_readable_number(number: int) -> str:
    suffixes = ['', 'K', 'M', 'B', 'T', 'P', 'E']
    number = float(number)

    for i, suffix in enumerate(suffixes):
        if abs(number) < 1000:
            return f"{number:.2f}{suffix}".rstrip('0').rstrip('.')
        number /= 1000.0

    return f"{number:.2e}"

class DotButtons(Gtk.Box):
    __gsignals__ = {
        Events.DEACTIVATE_COMPARISON: (GObject.SignalFlags.RUN_FIRST, None, ()),
        Events.VISUALIZE_DOT: (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        Events.SELECT_FUNC: (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
        Events.TOTAL_DYN_INST: (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, project_type: ProjectType, orientation=DotFileVisualizerOrientations.LEFT):

        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.project_type = project_type
        self.dot_files = []
        self.execution_info = None
        self.execution_info_collected = False
        self.sort_by_name_ascending = True
        self.sort_by_exec_ascending = True

        sort_order = Gtk.Box(spacing=20)
        sort_images = Gtk.Image.new_from_icon_name("view-sort-ascending", Gtk.IconSize.BUTTON)
        self.name_button = Gtk.Button(label="Name", image=sort_images)
        self.name_button.set_always_show_image(True)
        self.name_button.get_style_context().add_class(CSSClasses.NAME_BUTTON)
        self.name_button.connect(Events.CLICKED, self.sort_by_name)

        sort_images_exec = Gtk.Image.new_from_icon_name("view-sort-ascending", Gtk.IconSize.BUTTON)
        self.execution_button = Gtk.Button(label="Execution", image=sort_images_exec)
        self.execution_button.set_always_show_image(True)
        self.execution_button.get_style_context().add_class(CSSClasses.EXEC_BTN)

        self.execution_button.connect(Events.CLICKED, self.sort_by_exec)

        sort_order.pack_start(self.name_button, False, True, 0)
        sort_order.pack_start(self.execution_button, False, True, 0)

        search_entry = Gtk.Entry(placeholder_text=SEARCH_PLACEHOLDER_TEXT)
        search_entry.set_size_request(200, -1)
        search_entry.connect(Events.CHANGED, self.search_function)
        self.dot_files_box = Gtk.VBox()
        inner_box = Gtk.VBox()
        inner_box.pack_start(search_entry, False, True, 0)
        inner_box.pack_start(sort_order, False, True, 0)
        inner_box.pack_start(self.dot_files_box, False, True, 0)

        dots_scrolled_window = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                   vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        dots_scrolled_window.add(inner_box)
        dots_scrolled_window.set_size_request(200, -1)

        self.bin_files_box = Gtk.VBox()
        bins_scrolled_window = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                  vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        bins_scrolled_window.add(self.bin_files_box)
        bins_scrolled_window.set_size_request(150, -1)

        if self.project_type == ProjectType.SPEC or self.project_type == ProjectType.SPEC_TUNE:
            label = Gtk.Label(label="Binary Files:")
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            self.bin_files_box.pack_start(label, False, True, 10)
            self.bin_files_box.pack_start(separator, False, True, 0)

            pane = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
            if orientation == DotFileVisualizerOrientations.LEFT:
                pane.pack1(bins_scrolled_window, resize=True, shrink=False)
                pane.pack2(dots_scrolled_window, resize=True, shrink=False)
            else:
                pane.pack2(bins_scrolled_window, resize=True, shrink=False)
                pane.pack1(dots_scrolled_window, resize=True, shrink=False)
            self.pack_start(pane, True, True, 0)
        else:
            self.pack_start(dots_scrolled_window, True, True, 0)

        self.selected_bench_path = ""
        self.selected_function_button = None
        self.total_dyn_inst_count = 0

    def load_data(self, project_dir_pattern: str) -> None:
        if self.project_type == ProjectType.SPEC or self.project_type == ProjectType.SPEC_TUNE:
            for bench in glob(project_dir_pattern):
                self.add_bin_file_button(bench)
        else:
            # Start the execution info collection in a separate thread
            threading.Thread(target=self.collect_execution_info, args=(project_dir_pattern,), daemon=True).start()
            self.load_dot_files(project_dir_pattern)

    def load_dot_files(self, dot_files_dir: str) -> None:
        self.dot_files = glob(os.path.join(dot_files_dir, "*.dot"))
        if len(self.dot_files) == 0:
            ErrorWindow("No dot files found.")

        self.populate_dot_files_box()
        children = self.dot_files_box.get_children()

        if len(children) > 0:
            first = children[0]
            first.emit(Events.CLICKED)

        self.name_button.emit(Events.CLICKED)

    def add_bin_file_button(self, dot_files_dir: str):

        def button_clicked(button):
            self.selected_bench_path = dot_files_dir
            self.load_dot_files(dot_files_dir)

        btn_name = os.path.basename(dot_files_dir).split(".")[0]
        button = Gtk.Button(label=btn_name)
        button.get_style_context().add_class(CSSClasses.BUTTON_STYLE_2)
        button.connect(Events.CLICKED, button_clicked)
        self.bin_files_box.pack_start(button, False, True, 0)
        self.bin_files_box.show_all()

    def populate_dot_files_box(self) -> None:
        if len(self.dot_files) == 0:
            return

        # Clean up the dot files before sorting
        for widget in self.dot_files_box.get_children():
            self.dot_files_box.remove(widget)

        for dot_file in self.dot_files:
            # Extract func name from dot file path
            label_text = os.path.basename(dot_file)[:-4]

            if self.execution_info_collected:
                label_text += f" ({human_readable_number(self.execution_info.get(label_text, 0))})"

            button_label = Gtk.Label(label=label_text, halign=Gtk.Align.START)
            button = Gtk.Button()
            button.add(button_label)

            if self.selected_function_button and label_text == self.selected_function_button.get_child().get_text():
                button.get_style_context().add_class(CSSClasses.SELECTED_BUTTON)
                self.selected_function_button = button
            else:
                button.get_style_context().add_class(CSSClasses.FUNCTION_NAME)

            button.connect(Events.CLICKED, self.dot_button_clicked, dot_file)
            self.dot_files_box.pack_start(button, False, True, 0)

        self.dot_files_box.show_all()

    def dot_button_clicked(self, button: Gtk.Button, dot_file: str) -> None:
        if self.selected_function_button:
            self.selected_function_button.get_style_context().remove_class(CSSClasses.SELECTED_BUTTON)
            self.selected_function_button.get_style_context().add_class(CSSClasses.FUNCTION_NAME)
            self.selected_function_button.queue_draw()

        button.get_style_context().add_class(CSSClasses.SELECTED_BUTTON)
        self.selected_function_button = button
        self.selected_function_button.queue_draw()
        selected_function_name = os.path.basename(dot_file)[:-4]

        self.emit(Events.SELECT_FUNC, selected_function_name, self.selected_bench_path)
        self.emit(Events.VISUALIZE_DOT, dot_file)

    def collect_execution_info(self, project_dir: str) -> None:
        bbe_parser = BBEFileParser(project_dir)
        self.execution_info = bbe_parser.extract_total_exec_info_for_each_func()
        if self.execution_info is None:
            self.execution_button.set_sensitive(False)
            self.execution_button.set_tooltip_text("Cannot find bbe.info file.")
            self.emit(Events.DEACTIVATE_COMPARISON)
            return

        self.execution_info_collected = True
        self.emit(Events.TOTAL_DYN_INST, human_readable_number(self.execution_info.get(TOTAL_DYN_INST, 0)))

    def sort_by_name(self, button: Gtk.Button) -> None:
        self.dot_files.sort(reverse=not self.sort_by_name_ascending)
        self.sort_by_name_ascending = not self.sort_by_name_ascending

        icon_name = "view-sort-ascending" if self.sort_by_name_ascending else "view-sort-descending"
        button.get_image().set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)

        self.populate_dot_files_box()

    def sort_by_exec(self, button: Gtk.Button) -> None:
        if not self.execution_info_collected:
            ErrorWindow("Execution information is still being collected.")
            return

        self.dot_files.sort(key=lambda f: self.execution_info.get(os.path.basename(f)[:-4], 0),
                            reverse=not self.sort_by_exec_ascending)

        self.sort_by_exec_ascending = not self.sort_by_exec_ascending

        icon_name = "view-sort-ascending" if  self.sort_by_exec_ascending else "view-sort-descending"
        button.get_image().set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)

        self.populate_dot_files_box()

    def search_function(self, entry: Gtk.Entry) -> None:
        search_text: str = entry.get_text().lower()

        for dot_file_widget in self.dot_files_box.get_children():
            dot_file_name: str = dot_file_widget.get_child().get_text().lower()
            if search_text in dot_file_name:
                dot_file_widget.show()
            else:
                dot_file_widget.hide()

    def get_num_of_funcs(self) -> int:
        return len(self.dot_files)



class DotFileVisualizer(Gtk.Box):
    __gsignals__ = {
        Events.DEACTIVATE_COMPARISON: (GObject.SignalFlags.RUN_FIRST, None, ()),
        Events.SELECT_FUNC: (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
    }

    def __init__(self, orientation: DotFileVisualizerOrientations,
                 line_pos: int, project_type: ProjectType) -> None:

        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.selected_bench = ""
        self.selected_func = ""
        self.project_dir = ""
        self.total_dyn_inst = ""

        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, position=line_pos)
        self.pack_start(self.paned, True, True, 0)

        self.xdot_widget = xdot.ui.DotWidget()
        self.xdot_widget.set_size_request(500, -1)
        self.xdot_widget.get_style_context().add_class(CSSClasses.XDOT_WIDGET)

        self.dot_buttons = DotButtons(project_type, orientation)
        self.dot_buttons.connect(Events.VISUALIZE_DOT, self.visualize_graph)
        self.dot_buttons.connect(Events.DEACTIVATE_COMPARISON, lambda _: self.emit(Events.DEACTIVATE_COMPARISON))
        self.dot_buttons.connect(Events.SELECT_FUNC, self.select_function)
        self.dot_buttons.connect(Events.TOTAL_DYN_INST, self.set_total_dyn_inst)
        self.dot_buttons.get_style_context().add_class(CSSClasses.GRAPH_VIS_LEFT_PANEL)

        if orientation == DotFileVisualizerOrientations.RIGHT:
            self.paned.pack1(self.xdot_widget, resize=True, shrink=False)
            self.paned.pack2(self.dot_buttons, resize=True, shrink=False)
            align = Gtk.Align.END
        else:
            self.paned.pack1(self.dot_buttons, resize=True, shrink=False)
            self.paned.pack2(self.xdot_widget, resize=True, shrink=False)
            align = Gtk.Align.START

        self.summary_info_label = Gtk.Label(halign=align)
        self.summary_info_label.get_style_context().add_class(CSSClasses.SUMMARY_INFO)
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        summary_box.pack_start(self.summary_info_label, False, False, 0)

        self.pack_end(summary_box, False, False, 0)

    def load_data(self, project_dir_pattern: str):
        self.project_dir = project_dir_pattern
        self.dot_buttons.load_data(project_dir_pattern)

    def select_function(self, event, func, bench_path):
        self.selected_func = func
        self.selected_bench = bench_path
        self.emit(Events.SELECT_FUNC, func, bench_path)

        summary_info = ""
        if len(self.total_dyn_inst) > 0:
            summary_info = f"total_dyn_inst_count: {self.total_dyn_inst} | "
        
        summary_info += f"number_of_funcs: {self.dot_buttons.get_num_of_funcs()} | func: "

        if len(bench_path) > 0:
            bench_name = os.path.basename(bench_path).split("_")[0]
            summary_info += f"{bench_name} --> {func}"
        else:
            summary_info += func

        self.summary_info_label.set_label(summary_info)

    def set_total_dyn_inst(self, event, number: str):
        self.total_dyn_inst = number

    def visualize_graph(self, button: Gtk.Button, dot_file_path: str) -> None:
        try:
            with open(dot_file_path, 'rb') as file:
                dot_code: bytes = file.read()
                self.xdot_widget.set_dotcode(dot_code)

        except FileNotFoundError:
            ErrorWindow(f"Error: DOT file not found: {dot_file_path}")
        except Exception as e:
            ErrorWindow(f"Error: Unexpected Error: {e}")


class DotVisualizerWindow(MultiWindow):
    def __init__(self, project_dir: str, project_type: ProjectType) -> None:
        super().__init__(title=WINDOW_BASE_TITLE,
                         default_width=DOT_WINDOW_WIDTH,
                         default_height=DOT_WINDOW_HEIGHT)
        self.maximize()
        self.project_dir = project_dir
        self.project_type = project_type

        self.main_box = Gtk.VBox()
        self.add(self.main_box)
        self.menu_bar: Optional[Gtk.MenuBar] = None
        self.compare_option = Gtk.MenuItem(label="Compare")
        self.evaluate_option = Gtk.MenuItem(label="Evaluate")
        if project_type != ProjectType.SPEC_TUNE:
            self.evaluate_option.set_sensitive(False)
            self.evaluate_option.set_tooltip_text("This option only works when comparing projects.")

        self.plugins_manager = PluginsManager(project_dir)
        self.create_menu()
        self.visualizers_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(self.visualizers_paned, True, True, 0)
        self.visualizers: List[Optional[DotFileVisualizer]] = [None, None]

        if self.project_type == ProjectType.SPEC_TUNE:
            self.add_visualizer(os.path.join(project_dir, "*_base*_dots"))
            self.add_visualizer(os.path.join(project_dir, "*_pick*_dots"))
        elif project_type == ProjectType.SPEC:
            self.add_visualizer(os.path.join(project_dir, "*_dots"))
        else:
            self.add_visualizer(project_dir)

        self.show_all()

    def add_visualizer(self, project_dir) -> None:
        if self.visualizers[1] is not None:
            self.visualizers_paned.remove(self.visualizers[1])

        if self.visualizers[0] is None:
            new_visualizer = DotFileVisualizer(DotFileVisualizerOrientations.LEFT,
                                               PANE_SEPERATOR_POS, self.project_type)
            self.visualizers[0] = new_visualizer
            self.visualizers_paned.pack1(new_visualizer, resize=True, shrink=False)
        else:
            if self.visualizers[1] is not None:
                self.visualizers_paned.remove(self.visualizers[1])

            new_visualizer = DotFileVisualizer(DotFileVisualizerOrientations.RIGHT,
                                               PANE_SEPERATOR_POS, self.project_type)
            self.visualizers[1] = new_visualizer
            self.visualizers_paned.pack2(new_visualizer, resize=True, shrink=False)

        new_visualizer.connect(Events.DEACTIVATE_COMPARISON, self.deactivate_comparison)
        new_visualizer.connect(Events.SELECT_FUNC, self.select_function)
        new_visualizer.load_data(project_dir)
        new_visualizer.show_all()

    def deactivate_comparison(self, button: Gtk.Button) -> None:
        self.compare_option.set_sensitive(False)
        self.compare_option.set_tooltip_text("Cannot find .bbexec file.")
        self.compare_option.get_style_context().add_class("deactivate_comparison")

    def select_function(self, event, func, bench_path) -> None:
        self.plugins_manager.set_current_func(func, bench_path)

    def create_menu(self) -> None:
        self.menu_bar = Gtk.MenuBar()
        self.setup_file_menu()
        self.setup_plugins_menu()
        self.setup_evaluate_menu()
        self.setup_help_menu()
        self.main_box.pack_start(self.menu_bar, False, False, 0)

    def setup_file_menu(self) -> None:
        def on_new_proj_activated(widget, event):
            self.new_proj_activated(widget, event)
            return True

        def on_compare_activate(widget, event):
            self.on_compare_activate(widget)
            return True

        new_item = Gtk.MenuItem(label="New")

        new_item.connect(Events.BUTTON_PRESS, on_new_proj_activated)
        self.compare_option.connect(Events.BUTTON_PRESS, on_compare_activate)

        self.menu_bar.add(new_item)
        self.menu_bar.add(self.compare_option)

    @staticmethod
    def new_proj_activated(widget: Gtk.Widget, e) -> None:
        from asm_gui import ASMGWindow

        new_win = ASMGWindow()
        new_win.setup_workplace()
        new_win.setup_main_view()
        new_win.setup_recent_projects_view()
        new_win.setup_new_project_view()
        new_win.show_all()

    def on_compare_activate(self, widget):
        new_proj_dir = self.project_dir + f"{uuid.uuid4().hex}_cmp"
        compare_window = CompareWindow(self.project_dir, new_proj_dir)
        compare_window.connect(Events.COMPARE, lambda _: self.add_visualizer(new_proj_dir))
        compare_window.show_all()
        self.evaluate_option.set_sensitive(True)

    def setup_plugins_menu(self) -> None:
        plugins_menu_item = self.plugins_manager.create_plugins_menu()
        self.menu_bar.append(plugins_menu_item)

    def evaluate_bbes(self):
        command_builder = CommandBuilder()
        if self.project_type == ProjectType.BASIC:
            first_bbe_dir = self.visualizers[0].project_dir
            second_bbe_dir = self.visualizers[1].project_dir
        else:
            first_bbe_dir = self.visualizers[0].selected_bench
            second_bbe_dir = self.visualizers[1].selected_bench

            if not first_bbe_dir or not second_bbe_dir:
                ErrorWindow("Cannot find .bbexec files for evaluation.")
                return

        xlsx_path = os.path.join(DOWNLOADS_DIR, f"{uuid.uuid4().hex}evaluation_result.xlsx")

        command = command_builder.make_evaluation_command(first_bbe_dir, second_bbe_dir, xlsx_path)
        ret_code = command_builder.execute(command)
        if ret_code == 0:
            command = f"xdg-open {xlsx_path}"
            if command_builder.execute(command) != 0:
                ErrorWindow(f"Failed to open {xlsx_path}")
        else:
            ErrorWindow(f"While evaluating {first_bbe_dir} and {second_bbe_dir}.")

    def setup_evaluate_menu(self) -> None:
        self.evaluate_option.connect(Events.ACTIVATE,
                                     lambda _: threading.Thread(target=self.evaluate_bbes, daemon=True).start())
        self.menu_bar.append(self.evaluate_option)

    def setup_help_menu(self) -> None:
        def on_help_window_clicked(widget, event):
            HelpWindow().show_all()
            return True

        help_menu_item = Gtk.MenuItem(label="Help")
        help_menu_item.connect(Events.BUTTON_PRESS, on_help_window_clicked)
        self.menu_bar.append(help_menu_item)


class CompareWindow(Gtk.Window):
    __gsignals__ = {
        Events.COMPARE: (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, old_proj_dir, new_proj_dir: str) -> None:
        super().__init__(title="Compare", default_width=700, default_height=200)
        self.old_proj_dir = old_proj_dir
        self.new_proj_dir = new_proj_dir

        main_box = Gtk.VBox()
        main_box.get_style_context().add_class(CSSClasses.MAIN_BOX)
        self.add(main_box)

        self.asm_path = FileSelectorBox(ViewsLabels.ASM_PATH)
        self.asm_path.label_widget.set_width_chars(16)

        self.bbexec_path = FileSelectorBox(ViewsLabels.BBEXEC_PATH)
        self.bbexec_path.label_widget.set_width_chars(16)

        self.singleton = CheckBox(ViewsLabels.SINGLETON)
        self.singleton.get_style_context().add_class(CSSClasses.ACTION_BOX)

        self.command_builder = CommandBuilder()
        compare_proj_button = Gtk.Button(label="Compare")
        compare_proj_button.connect(Events.CLICKED, self.compare)
        compare_proj_button.get_style_context().add_class(CSSClasses.COMPARE_BTN)

        main_box.pack_start(self.asm_path, False, False, 5)
        main_box.pack_start(self.bbexec_path, False, False, 5)
        main_box.pack_start(self.singleton, False, False, 5)
        main_box.pack_start(compare_proj_button, False, False, 5)

    def validate_and_get_input_values(self):
        values = {}
        values[ViewsLabels.ASM_PATH] = self.asm_path.get_text()

        values[ViewsLabels.LOCATION] = self.new_proj_dir
        if self.bbexec_path.has_valid_input():
            values[ViewsLabels.BBEXEC_PATH] = self.bbexec_path.get_text()
        else:
            return None

        values[ViewsLabels.SINGLETON] = self.singleton.get_active()

        return values

    def compare(self, button: Gtk.Button):
        try:
            values = self.validate_and_get_input_values()
            cmd = self.command_builder.make_visualize_command(values)
            if not cmd:
                raise Exception("Command was not created.")

            return_code: int = self.command_builder.execute(cmd)
            if return_code == 0:
                self.emit(Events.COMPARE)
            else:
                raise Exception(f"Command executed failed with exit code {return_code}")
        except Exception as e:
            ErrorWindow(str(e))
        finally:
            self.destroy()
