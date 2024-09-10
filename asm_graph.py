#!/usr/bin/env python3

# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import json
import os
import argparse
import subprocess
import shutil
import glob

from alive_progress import alive_bar
from argparse import Namespace
from typing import Dict, NoReturn

from plugins.helper import run_selected_plugins, load_plugins, add_plugin
from src.asm_parser import parse_function_asm
from src.bbe_parser import BBEFileParser
from src.funcs_black_list import load_blacklist
from src.opcodes import MAX_FUNCTION_NAME_LENGTH
from src.graph import FlowGraph
from src.ui.constants import ROOT_DIR, PLUGINS_JSON
from src.xlsx_writer import XLSXWriter

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(CUR_DIR, "output")
XLSX_SINGLETONS_FILE_NAME = "singletons.xlsx"


def disassemble_bin_to_asm(binary: str, objdump_path: str) -> str:
    print("Disassembling binary to asm.")
    file_path = os.path.join(OUT_DIR, os.path.basename(binary) + ".asm")
    try:
        with open(file_path, 'w') as asm_file:
            subprocess.check_call([objdump_path, "-d", "--no-show-raw-insn", binary], stdout=asm_file)
    except subprocess.CalledProcessError as msg:
        print(msg)
        exit(1)

    return file_path


def load_funcs(asm_path: str, func_name: str = None) -> Dict[str, str]:
    with open(asm_path, "r") as asm:
        lines = asm.readlines()

    lines = [line.strip() for line in lines if line.strip()]
    asm_funcs = {}
    curr_func_name = ""
    curr_func_content = ""
    text_section = False
    black_list = load_blacklist()

    for line in lines:
        if not text_section:
            if line == "Disassembly of section .text:":
                text_section = True
            continue

        if line.startswith("Disassembly of section"):
            break

        if line.endswith(">:"):
            if curr_func_content:
                if (func_name == "all" and func_name not in black_list) or (func_name == curr_func_name):
                    asm_funcs[curr_func_name] = curr_func_content
                curr_func_content = ""
            curr_func_name = line.split()[-1].strip("<>:")

        if (func_name == "all" and func_name not in black_list) or (func_name == curr_func_name):
            curr_func_content += line + "\n"

    if (func_name == "all" and func_name not in black_list) or (func_name == curr_func_name):
        asm_funcs[curr_func_name] = curr_func_content

    assert asm_funcs, "Cannot load functions."
    return asm_funcs


def parse_arguments() -> Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-a", "--asm", type=str, help="Path to the assembly file.")
    group.add_argument("-b", "--bin", type=str, help="Path to the binary file.")
    parser.add_argument("-d", "--objdump", type=str, help="Path to the disassembler (riscv-**objdump).")
    parser.add_argument("-f", "--func", type=str, default="all",
                        help="The name of the function that should be extracted.\n"
                             "By default will produce all functions from the text segment.")
    parser.add_argument("-c", "--bbexec", type=str, help="Path to the bbexec file or " \
                                                                      "to the dir with bbexec files.")
    parser.add_argument("--dot", action="store_true", help="Create dot graphs for functions.")
    parser.add_argument("--min_exec_count", type=int, default=1000000,
                        help="Minimum number of times BB must be executed to process it with plugins.")
    parser.add_argument("-s", "--singletons", action="store_true",
                        help=f"Collect singleton basic blocks into the {XLSX_SINGLETONS_FILE_NAME}.")
    parser.add_argument("-o", "--output", type=str, default=OUT_DIR,
                        help=f"The name of the out directory. (by default: {OUT_DIR})")

    parser.add_argument("--run_plugins", dest="plugins", action="store_true",
                        help=f"Run the enabled plugins from plugins/plugins.json")

    group.add_argument("--add_plugin", type=str, nargs=2, metavar=('PLUGIN_NAME', 'PLUGIN_PATH'),
                        help="Add a custom plugin. Provide plugin name and file path.\n"
                             "File must contain a 'run' function with a 'Node' object as input "
                             "(see plugins/example.py).")

    parsed_args = parser.parse_args()
    if parsed_args.bin and not parsed_args.objdump:
        parser.error('--objdump is required when --bin is set.')

    return parsed_args


def process_function(args: Namespace,
                     function_name: str,
                     func_content: str,
                     bbe_parser: BBEFileParser,
                     xlsx_for_singletons: XLSXWriter,
                     xlsx_for_plugins: XLSXWriter,
                     plugins_data=None) -> NoReturn:
    if len(function_name) > MAX_FUNCTION_NAME_LENGTH:
        function_name = function_name[-MAX_FUNCTION_NAME_LENGTH:]

    if not func_content:
        print(f"Asm content for {function_name} is empty!")
        exit(1)

    asm_code = parse_function_asm(func_content)
    graph = FlowGraph(asm_code)

    if bbe_parser:
        addresses = graph.get_bb_addresses()
        graph.usage_info = bbe_parser.extract_usage_info(addresses)

    graph.set_nodes_usage_info()

    if args.dot:
        dot_file = os.path.join(OUT_DIR, function_name + ".dot")
        try:
            graph.draw_graph(dot_file)
        except TimeoutError:
            print("Time is out for func: ", function_name)
        except Exception as ex:
            print(str(ex))
            return

    if args.singletons:
        graph.find_singleton_bbs()
        xlsx_for_singletons.append(graph, function_name)

    if plugins_data:
        for node in graph.nodes:
            count = node.get_execution_count()
            if args.bbexec and (count == 0 or int(count) < args.min_exec_count):
                continue
            run_selected_plugins(node, function_name, plugins_data, xlsx_for_plugins)


def main(args: Namespace):
    global OUT_DIR
    OUT_DIR = args.output

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    if args.bin and args.objdump:
        assert os.path.exists(args.bin), f"Cannot find binary file: {args.bin}. No such file."
        assert os.path.exists(args.objdump), f"Cannot find disassembler(objdump): {args.objdump}. No such file."

        asm_path = disassemble_bin_to_asm(args.bin, args.objdump)
    elif args.asm:
        assert os.path.exists(args.asm), f"Cannot find asm file: {args.asm}"

        asm_path = args.asm
        try:
            shutil.copy(asm_path, os.path.join(OUT_DIR, os.path.basename(asm_path)))
        except Exception as e:
            print(f"Warning: Cannot copy asm file to output dir: {e}")

    else:
        plugin_name = args.add_plugin[0]
        plugin_file = args.add_plugin[1]
        try:
            add_plugin(plugin_name, plugin_file)
        except Exception as e:
            print(str(e))
        return 0


    bbe_parser = None
    if args.bbexec:
        assert os.path.exists(args.bbexec), f"Cannot find bbexec file: {args.bbexec}. No such file or directory."
        bbe_parser = BBEFileParser(OUT_DIR)
        if os.path.isdir(args.bbexec):
            bbe_files = glob.glob(os.path.join(args.bbexec, "*.bbexec"))
            bbe_parser.parse_and_save_data(bbe_files)
            for bbe_file in bbe_files:
                try:
                    shutil.copy(bbe_file, os.path.join(OUT_DIR, os.path.basename(bbe_file)))
                except Exception as e:
                    print(f"Warning: Cannot copy bbexec file to output dir: {e}")
        else:
            bbe_parser.parse_and_save_data([args.bbexec])
            try:
                shutil.copy(args.bbexec, os.path.join(OUT_DIR, os.path.basename(args.bbexec)))
            except Exception as e:
                print(f"Warning: Cannot copy bbexec file to output dir: {e}")

    xlsxwriter_singletons = None
    if args.singletons:
        singletons_path = os.path.join(OUT_DIR, XLSX_SINGLETONS_FILE_NAME)
        xlsxwriter_singletons = XLSXWriter(singletons_path)
        xlsxwriter_singletons.create_asm_sheet()

    xlsxwriter_checkers = None
    plugins_data = None
    if args.plugins:
        plugins_data = load_plugins()
        checker_xlsx_name = f"{os.path.basename(asm_path)}.xlsx"
        checker_xlsx_path = os.path.join(OUT_DIR, checker_xlsx_name)
        xlsxwriter_checkers = XLSXWriter(checker_xlsx_path)

    asm_funcs = load_funcs(asm_path, args.func)

    with alive_bar(len(asm_funcs)) as bar:
        for function_name, content in asm_funcs.items():
            process_function(args, function_name, content, bbe_parser,
                             xlsxwriter_singletons, xlsxwriter_checkers,
                             plugins_data)
            bar()

    if args.plugins:
        # Sort by before last column
        xlsxwriter_checkers.dump(-2)

    # FIXME: US 113
    # We collect all execution info and dump in file at the end
    # if args.collect:
    #    collect_parser.print_info_from_collect()

    if args.singletons:
        # Sort by the last column
        xlsxwriter_singletons.dump(-1)


if __name__ == '__main__':
    main(parse_arguments())
