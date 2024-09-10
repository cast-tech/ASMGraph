# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import os
import json
import importlib
import inspect
from typing import List, get_type_hints

from src.graph import Node
from src.asm_parser import parse_function_asm
from src.graph import FlowGraph
from src.ui.constants import ROOT_DIR, BASIC_PLUGINS, PLUGINS_JSON, CUSTOM_PLUGIN_FUNCTION_NAME


def load_module_from_file(file_path: str):
    if not os.path.isfile(file_path):
        return None

    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def get_function_from_module(module, function_name):
    return getattr(module, function_name, None)


def validate_plugin_func(func) -> bool:
    expected_args = 1
    expected_arg_type = Node
    expected_return_type = List[dict]

    sig = inspect.signature(func)
    if len(sig.parameters) != expected_args:
        return False

    arg_name, param = next(iter(sig.parameters.items()))
    if param.annotation is not inspect.Signature.empty and param.annotation is not expected_arg_type:
        return False

    if sig.return_annotation is not inspect.Signature.empty:
        resolved_return_type = get_type_hints(func).get('return', None)
        if resolved_return_type != expected_return_type:
            return False

    return True

def validate_plugin(plugin_file):
    if not os.path.isfile(plugin_file):
        raise ValueError("Error: Cannot find plugin file " + plugin_file)

    plugin_module = load_module_from_file(plugin_file)
    function = get_function_from_module(plugin_module, CUSTOM_PLUGIN_FUNCTION_NAME)

    if not function:
        raise ValueError(f"Function '{CUSTOM_PLUGIN_FUNCTION_NAME}' not found in {plugin_file}.")

    if not callable(function):
        raise ValueError(f"Function '{CUSTOM_PLUGIN_FUNCTION_NAME}' is not callable.")

    if not validate_plugin_func(function):
        raise ValueError(f"Function '{CUSTOM_PLUGIN_FUNCTION_NAME}' has invalid signature.")


def apply_plugins_to_func(func_name, func_content, plugins_data, xlsx_writer):
    parsed_asm_code = parse_function_asm(func_content)
    graph = FlowGraph(parsed_asm_code)
    for g_node in graph.nodes:
        run_selected_plugins(g_node, func_name, plugins_data, xlsx_writer)


def run_selected_plugins(basic_block, func_name, plugins_data, xlsx_writer) -> None:
    plugins_file_path = os.path.join(ROOT_DIR, "plugins", BASIC_PLUGINS)
    base_module = load_module_from_file(plugins_file_path)

    for plugin_info in plugins_data:
        if plugin_info.get("enabled", False):
            plugin_name = plugin_info.get("name", None)
            file_path = plugin_info.get("file", None)
            if file_path:
                module = load_module_from_file(file_path)
            else:
                module = base_module

            function_name = plugin_info["function"]
            function = get_function_from_module(module, function_name)
            if not function:
                print(f"ERROR: Cannot find function {function_name} for plugin {plugin_name}.")
                continue

            args = [basic_block] + plugin_info["args"]
            try:
                res = function(*args)
                if res:
                    xlsx_writer.append_checker_result(plugin_name, func_name, basic_block, res)
            except Exception as e:
                print(f"ERROR: Running plugin {plugin_name}: {e}")


def load_plugins():
    plugins_path = os.path.join(ROOT_DIR, "plugins", PLUGINS_JSON)
    with open(plugins_path, 'r') as plugins_file:
        return json.load(plugins_file)

def save_plugins(plugins_data):
    plugins_path = os.path.join(ROOT_DIR, "plugins", PLUGINS_JSON)
    with open(plugins_path, 'w') as json_file:
        json.dump(plugins_data, json_file, indent=2)

def add_plugin(plugin_name, plugin_file):
    plugin_file = os.path.abspath(plugin_file)
    try:
        validate_plugin(plugin_file)
        plugins_data = load_plugins()

        for plugin_info in plugins_data:
            if plugin_info["name"] == plugin_name:
                print(f"Failed adding plugin: Plugin '{plugin_name}' already exists.")
                return

        plugins_data.append({
            "name": plugin_name,
            "enabled": False,
            "function": CUSTOM_PLUGIN_FUNCTION_NAME,
            "file": plugin_file,
            "args": [],
        })
        save_plugins(plugins_data)
    except Exception as e:
        raise e
