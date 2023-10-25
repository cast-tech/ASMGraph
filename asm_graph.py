#!/usr/bin/env python3

import os
import argparse
import subprocess
from alive_progress import alive_bar

from src.asm_parser import parse_asm_file
from src.collect_parser import CollectFileParser
from src.opcodes import MAX_FUNCTION_NAME_LENGTH
from src.graph import FlowGraph
from src.xlsx_writer import XLSXWriter
from src.fusion import process_basic_block

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(CUR_DIR, "output")
XLSX_SINGLETONS_FILE_NAME = "singletons.xlsx"


def disassemble_bin_to_asm(binary, objdump_path):
    print("Disassembling binary to asm.")
    file_path = os.path.join(OUT_DIR, os.path.basename(binary) + ".asm")
    try:
        with open(file_path, 'w') as asm_file:
            subprocess.check_call([objdump_path, "-d", "--no-show-raw-insn", binary], stdout=asm_file)
    except subprocess.CalledProcessError as msg:
        print(msg)
        exit(1)

    return file_path


def load_funcs(asm_path, func_name=None):
    assert os.path.exists(asm_path), f"Cannot find asm file: {asm_path}"

    with open(asm_path, "r") as asm:
        lines = asm.readlines()

    lines = [line.strip() for line in lines if line.strip()]
    asm_funcs = {}

    curr_func_name = ""
    curr_func_content = ""
    text_section = False

    for line in lines:
        if not text_section:
            if line == "Disassembly of section .text:":
                text_section = True
            continue

        if line.startswith("Disassembly of section"):
            break

        if line.endswith(">:"):
            if curr_func_content:
                if not func_name or func_name == curr_func_name:
                    asm_funcs[curr_func_name] = curr_func_content
                curr_func_content = ""
            curr_func_name = line.split()[-1].strip("<>:")

        if not func_name or func_name == curr_func_name:
            curr_func_content += line + "\n"

    if not func_name or func_name == curr_func_name:
        asm_funcs[curr_func_name] = curr_func_content

    assert asm_funcs, "Cannot load functions."
    return asm_funcs


def parse_arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-a", "--asm", type=str, help="Path to the assembler file.")
    group.add_argument("-b", "--bin", type=str, help="Path to the binary file.")
    parser.add_argument("-d", "--objdump", type=str, help="Path to the disassembler (riscv-**objdump).")
    parser.add_argument("-f", "--func", type=str, default="all",
                        help="The name of the function that should be extracted.\n"
                             "By default will produce all functions from the text segment.")
    parser.add_argument("-c", "--collect", type=str, help="Path to the collect file.")
    parser.add_argument("-i", "--fusion",  action="store_true", help="Check instruction fusion.")
    parser.add_argument("--dot", action="store_true", help="Create dot graph for functions.")
    parser.add_argument("--min_exec_count", type=int, default=1000000,
                        help="BB should have at least mentioned amount execution count to be processed in fusion checkers.")
    parser.add_argument("-s", "--singletons", action="store_true",
                        help=f"Collect singleton basic blocks into the {XLSX_SINGLETONS_FILE_NAME}.")
    parser.add_argument("-o", "--output", type=str, default=OUT_DIR,
                        help=f"The name of the out directory. (by default: {OUT_DIR})")

    parsed_args = parser.parse_args()
    if parsed_args.bin and not parsed_args.objdump:
        parser.error('--objdump is required when --bin is set.')

    return parsed_args


def process_function(args, function_name, func_content, collect_parser,
                     xlsx_for_singletons, xlsx_for_fusions):
    if len(function_name) > MAX_FUNCTION_NAME_LENGTH:
        function_name = function_name[-MAX_FUNCTION_NAME_LENGTH:]

    func_file_path = os.path.join(OUT_DIR, function_name + ".asm")
    with open(func_file_path, "w") as file:
        file.write(func_content)

    asm_code = parse_asm_file(func_file_path)
    graph = FlowGraph(asm_code)

    if args.collect:
        addresses = graph.get_bb_addresses()
        graph.usage_info = collect_parser.extract_usage_info(addresses)

    graph.set_nodes_usage_info()

    if args.dot:
        dot_file = os.path.join(OUT_DIR, function_name + ".dot")
        try:
            graph.draw_graph(dot_file)
        except Exception:
            print("Time is out for func: ", function_name)
            return

    if args.singletons:
        graph.find_singleton_bbs()
        xlsx_for_singletons.append(graph, function_name)

    if args.fusion:
        for node in graph.nodes:
            count = node.get_execution_count()
            if args.collect and (count == 'empty' or int(count) < args.min_exec_count):
                continue

            process_basic_block(node, function_name, xlsx_for_fusions)


def main(args):
    global OUT_DIR
    OUT_DIR = args.output

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    asm_path = ""
    if args.bin and args.objdump:
        assert os.path.exists(args.bin), f"Cannot find binary file: {args.bin}. No such file."
        assert os.path.exists(args.objdump), f"Cannot find disassembler(objdump): {args.objdump}. No such file."

        asm_path = disassemble_bin_to_asm(args.bin, args.objdump)
    elif args.asm:
        asm_path = args.asm

    collect_parser = None
    if args.collect:
        assert os.path.exists(args.collect), f"Cannot find collect file: {args.collect}. No such file."
        collect_parser = CollectFileParser(args.collect)
        collect_parser.parse_collect_file()

    xlsxwriter_singletons = None
    if args.singletons:
        singletons_path = os.path.join(OUT_DIR, XLSX_SINGLETONS_FILE_NAME)
        xlsxwriter_singletons = XLSXWriter(singletons_path)
        xlsxwriter_singletons.create_asm_sheet()

    xlsxwriter_checkers = None
    if args.fusion:
        checker_xlsx_name = f"{os.path.basename(asm_path)}.xlsx"
        checker_xlsx_path = os.path.join(OUT_DIR, checker_xlsx_name)
        xlsxwriter_checkers = XLSXWriter(checker_xlsx_path)

    if args.func == "all":
        asm_funcs = load_funcs(asm_path)
    else:
        asm_funcs = load_funcs(asm_path, args.func)

    with alive_bar(len(asm_funcs)) as bar:
        for function_name, content in asm_funcs.items():
            process_function(args, function_name, content, collect_parser,
                             xlsxwriter_singletons, xlsxwriter_checkers)
            bar()

    # We collect all fusion cases and dump in file at the end
    if args.fusion:
        # Sort by before last column
        xlsxwriter_checkers.dump(-2)

    # We collect all execution info and dump in file at the end
    if args.collect:
        collect_parser.print_info_from_collect()

    if args.singletons:
        # Sort by the last column
        xlsxwriter_singletons.dump(-1)


if __name__ == '__main__':
    main(parse_arguments())
