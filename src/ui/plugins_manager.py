# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import glob
import os
import threading
from uuid import uuid4
import subprocess
from typing import Optional, List

from asm_graph import load_funcs
from plugins.helper import apply_plugins_to_func, load_plugins, save_plugins, validate_plugin
from src.xlsx_writer import XLSXWriter
from src.ui.action_boxes import TextBox, FileSelectorBox
from src.ui.constants import CUSTOM_PLUGIN_FUNCTION_NAME, DOWNLOADS_DIR
from src.ui.error_handler import ErrorWindow
from src.ui.keywords import CSSClasses

from gi.repository import Gtk


class PluginsManager:
    def __init__(self, work_dir: str) -> None:
        self.selected_func = ""
        self.work_dir = work_dir
        self.plugins_data = None

        self.xlsx_writer: Optional[XLSXWriter] = None

        self.plugins_menu_item = None
        self.run_on_function_option = Gtk.MenuItem(label="Run on function")
        self.run_on_function_option.get_style_context().add_class(CSSClasses.RUN_PLUGINS_MENU_ITEM)
        self.run_on_function_option.set_sensitive(False)
        self.run_on_function_option.set_tooltip_text("Select a function.")

        self.run_on_file_option = Gtk.MenuItem(label="Run on file")
        self.run_on_file_option.get_style_context().add_class(CSSClasses.RUN_PLUGINS_MENU_ITEM)
        self.asm_file = self.get_asm_path()

        if len(self.asm_file) == 0:
            self.run_on_file_option.set_sensitive(False)
            self.run_on_file_option.set_tooltip_text("Select a file.")

    def get_asm_path(self) -> str:
        asm_files: List[str] = glob.glob(os.path.join(self.work_dir, "*.asm"))
        if len(asm_files) != 1:
            return ""
        return asm_files[0]

    def set_current_func(self, cur_func_name: str, cur_asm_file_dir: str = ""):
        self.run_on_function_option.set_sensitive(True)
        self.selected_func = cur_func_name

        if cur_asm_file_dir:
            self.asm_file = glob.glob(os.path.join(cur_asm_file_dir, "*.asm"))[0]
            self.run_on_file_option.set_sensitive(True)

    # FIXME: When selects check box pop-up closes
    def create_plugins_menu(self) -> Gtk.MenuItem:
        self.plugins_menu_item = Gtk.MenuItem(label="Run Plugins")
        plugins_submenu = Gtk.Menu()
        plugins_submenu.get_style_context().add_class(CSSClasses.RUN_PLUGINS)

        self.plugins_data = load_plugins()
        if not self.plugins_data:
            ErrorWindow("While loading plugins.")
            return
        for plugin_info in self.plugins_data:
            plugin_item = self.create_plugin_menu_item(plugin_info.get("name"), plugin_info.get("enabled", False))
            plugins_submenu.append(plugin_item)

        separator = Gtk.SeparatorMenuItem()
        separator.get_style_context().add_class(CSSClasses.PLUGINS_SUBMODULE)

        add_new_plugin_item = Gtk.MenuItem(label="Add new")
        add_new_plugin_item.get_style_context().add_class(CSSClasses.RUN_PLUGINS_MENU_ITEM)

        add_new_plugin_item.connect("activate", self.add_new_plugin)
        self.run_on_function_option.connect("activate", self.run_on_function_activate)
        self.run_on_file_option.connect("activate", self.run_on_file_activate)

        plugins_submenu.append(separator)
        plugins_submenu.append(add_new_plugin_item)
        plugins_submenu.append(self.run_on_function_option)
        plugins_submenu.append(self.run_on_file_option)

        self.plugins_menu_item.set_submenu(plugins_submenu)
        return self.plugins_menu_item

    def create_plugin_menu_item(self, plugin_name: str, status: bool) -> Gtk.CheckMenuItem:
        plugin_item = Gtk.CheckMenuItem(label=plugin_name)
        plugin_item.set_active(status)
        plugin_item.connect("toggled", self.on_plugin_toggled, plugin_name)
        return plugin_item

    def on_plugin_toggled(self, widget, plugin_name) -> None:
        for plugin_info in self.plugins_data:
            if plugin_info.get("name") == plugin_name:
                plugin_info["enabled"] = widget.get_active()

    def add_new_plugin(self, widget: Gtk.CheckMenuItem) -> None:
        dialog = Gtk.Dialog(title="Add New Plugin",
                            transient_for=self.plugins_menu_item.get_toplevel(),
                            flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)

        plugin_name_entry = TextBox(label="Plugin Name:")
        plugin_file_entry = FileSelectorBox(label="Plugin File:")

        content_area = dialog.get_content_area()
        content_area.add(plugin_name_entry)
        content_area.add(plugin_file_entry)
        content_area.get_style_context().add_class(CSSClasses.NEW_PLUGIN_DIALOG)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            plugin_name = plugin_name_entry.get_text()
            plugin_file = plugin_file_entry.get_text()

            if not plugin_name or not plugin_file:
                ErrorWindow(f"Plugin name and file must be provided.")
            elif not plugin_file_entry.has_valid_input():
                ErrorWindow(f"Cannot find plugin file: {plugin_file}")
            else:
                for plugin_info in self.plugins_data:
                    if plugin_info.get("name") == plugin_name:
                        ErrorWindow(f"Plugin with name {plugin_name} already exists.")
                        return
                try:
                    validate_plugin(plugin_file)

                    self.plugins_data.append({
                        "name": plugin_name,
                        "enabled": False,
                        "function": CUSTOM_PLUGIN_FUNCTION_NAME,
                        "file": plugin_file,
                        "args": [],
                    })
                    threading.Thread(target=lambda: save_plugins(self.plugins_data), daemon=True).start()
                    plugin_item = self.create_plugin_menu_item(plugin_name, False)
                    submenu = self.plugins_menu_item.get_submenu()

                    for i, child in enumerate(submenu.get_children()):
                        if isinstance(child, Gtk.SeparatorMenuItem):
                            submenu.insert(plugin_item, i)
                            break

                    plugin_item.show()
                except Exception as e:
                    ErrorWindow(f"While adding plugin: {e}")
        dialog.destroy()

    @staticmethod
    def open_xlsx(xlsx_path: str) -> bool:
        args = ["xdg-open", xlsx_path]
        try:
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except Exception as e:
            ErrorWindow(str(e))
            return False

        if proc.wait() != 0:
            return False
        return True

    def run_on_function_activate(self, widget) -> None:
        def run():
            if not self.selected_func:
                ErrorWindow("No Function Selected.")
                return

            xlsx_file_path = os.path.join(DOWNLOADS_DIR, f"{uuid4().hex}plugin.xlsx")
            self.xlsx_writer = XLSXWriter(xlsx_file_path)

            asm_func = load_funcs(self.asm_file, self.selected_func)
            apply_plugins_to_func(self.selected_func, asm_func[self.selected_func],
                                  self.plugins_data, self.xlsx_writer)

            # FIXME: dump row_id?
            self.xlsx_writer.dump(-2)
            self.xlsx_writer = None
            self.open_xlsx(xlsx_file_path)

        threading.Thread(target=run, daemon=True).start()
        threading.Thread(target=lambda: save_plugins(self.plugins_data), daemon=True).start()

    def run_on_file_activate(self, widget) -> None:
        def run():
            xlsx_file_path = os.path.join(DOWNLOADS_DIR, f"{uuid4().hex}plugin.xlsx")
            self.xlsx_writer = XLSXWriter(xlsx_file_path)

            asm_funcs = load_funcs(self.asm_file, "all")
            for func_name, func_content in asm_funcs.items():
                apply_plugins_to_func(func_name, func_content, self.plugins_data, self.xlsx_writer)

            self.xlsx_writer.dump(-2)
            self.xlsx_writer = None
            self.open_xlsx(xlsx_file_path)

        threading.Thread(target=run, daemon=True).start()
        threading.Thread(target=lambda: save_plugins(self.plugins_data), daemon=True).start()

