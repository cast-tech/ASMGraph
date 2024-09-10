#!/usr/bin/env python3

# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************


import os
import glob
import argparse
import xlsxwriter
from argparse import Namespace
from typing import Dict, List, NoReturn

FIRST = "FIRST"
SECOND = "SECOND"
FUNCTION_NAME = "FUNCTION NAME"
DIFF = "DIFF (FIRST - SECOND)"
DIFF_IN_PERCENTS = "DIFF IN PERCENTS"
TOTAL = "TOTAL"
TEST_NAME = "TEST NAME"

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_RESULT_FILE_NAME = "evaluation_result.xlsx"


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ff", dest="first_bbe_file", type=str, default=None,
                        help="Path to first hot block file")
    parser.add_argument("--sf", dest="second_bbe_file", type=str, default=None,
                        help="Path to second hot block file")
    parser.add_argument("--fd", dest="first_bbes_dir", type=str, default=None,
                        help="Path to directory with first hot block files (with .bbeexec files)")
    parser.add_argument("--sd", dest="second_bbes_dir", type=str, default=None,
                        help="Path to directory with second hot block files (with .bbexec files)")
    parser.add_argument("--all", dest="create_functions_diff_sheet", action="store_true",
                        help="Also create a functions comparisons table.")
    parser.add_argument("-o", dest="output_file", type=str, default=None,
                        help=f"Path to the output file (by default {os.path.join(CUR_DIR, XLSX_RESULT_FILE_NAME)})")
    args = parser.parse_args()

    if not args.first_bbes_dir and not args.first_bbe_file:
        parser.error('--ff or --fd is required')

    if not args.second_bbes_dir and not args.second_bbe_file:
        parser.error('--sf or --sd is required')

    if args.first_bbe_file and not args.second_bbe_file or \
       not args.first_bbe_file and args.second_bbe_file:
        parser.error("First and second argument must be a file, please use"
                     " '--ff' and '--sf' options.")

    if args.first_bbes_dir and not args.second_bbes_dir or \
       not args.first_bbes_dir and args.second_bbes_dir:
        parser.error("First or second argument must be a directory, please use"
                     " '--fd' and '--sd' options.")

    return args


def get_functions_dyn_inst_count(bbe_file: str) -> [Dict[str, Dict]]:
    func_name_and_dyn_inst_count = {}

    with open(bbe_file, "r") as block_fp:
        for line in block_fp:
            line = line.strip()

            if not line.startswith("0x"):
                continue

            block_info = line.split()

            if len(block_info) == 4:
                function_name = block_info[3]
                if "." in function_name:
                    function_name = function_name.split(".")[0]

                if function_name in func_name_and_dyn_inst_count:
                    func_name_and_dyn_inst_count[function_name] += int(block_info[1])
                else:
                    func_name_and_dyn_inst_count[function_name] = int(block_info[1])

    sort_by_exec_count = sorted(func_name_and_dyn_inst_count.items(), key=lambda x: x[1], reverse=True)
    return dict(sort_by_exec_count)


def get_cmp_result(first_bbes_func_info: Dict[str, Dict],
                   second_bbes_func_info: Dict[str, Dict]) -> Dict[str, List]:
    result = {}

    for first_func_name, first_func_exec_count in first_bbes_func_info.items():
        same_second_func = second_bbes_func_info.get(first_func_name, -1)
        result[first_func_name] = [first_func_exec_count, same_second_func]

    return result

def prepare_header(workbook: xlsxwriter.Workbook,
                   sheet_name: str) -> xlsxwriter:
    ws = workbook.add_worksheet(sheet_name)

    row = 0
    col = 0

    ws.set_column(0, 0, 25)
    ws.set_column(1, 1, 15)
    ws.set_column(2, 2, 15)
    ws.set_column(3, 3, 15)
    ws.set_column(4, 4, 15)

    header_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bold': True,
        'italic': True
    })

    ws.write(row, col, FUNCTION_NAME, header_format)
    ws.write(row, col + 1, FIRST, header_format)
    ws.write(row, col + 2, SECOND, header_format)
    ws.write(row, col + 3, DIFF, header_format)
    ws.write(row, col + 4, DIFF_IN_PERCENTS, header_format)

    return ws


def create_diff_for_single_bbe(workbook: xlsxwriter.Workbook,
                                   file_name: str,
                                   blocks: Dict[str, List]) -> NoReturn:

    ws = prepare_header(workbook, file_name)

    row = 1
    first_dyn_inst_count = 0
    second_dyn_inst_count = 0

    for item, cost in blocks.items():

        diff_format = ''
        cost_difference = cost[0] - cost[1]
        diff_in_percent = round((cost_difference / cost[1]) * 100, 2)
        if cost_difference > 0:
            diff_format = workbook.add_format({'font_color': 'red'})

        ws.write(row, 0, item, diff_format)
        ws.write(row, 1, cost[0], diff_format)
        ws.write(row, 2, cost[1], diff_format)
        ws.write(row, 3, cost_difference, diff_format)
        ws.write(row, 4, diff_in_percent, diff_format)

        first_dyn_inst_count += cost[0]
        second_dyn_inst_count += cost[1]
        row += 1

    # At end add summary of whole dynamic instructions count

    row += 2
    bold = workbook.add_format({'bold': True})
    ws.write(row, 0, TOTAL, bold)
    ws.write(row, 1, first_dyn_inst_count, bold)
    ws.write(row, 2, second_dyn_inst_count, bold)
    ws.write(row, 3, first_dyn_inst_count - second_dyn_inst_count, bold)


def create_general_diff(workbook: xlsxwriter.Workbook,
                        bench_name: str,
                        first_dyn_inst_count: int,
                        second_dyn_inst_count: int,
                        general_diff_row: int) -> NoReturn:

    general_diff = workbook.get_worksheet_by_name("general_diff")
    if not general_diff:
        general_diff = workbook.add_worksheet("general_diff")

        general_diff.set_column(0, 0, 25)
        general_diff.set_column(1, 1, 20)
        general_diff.set_column(2, 2, 25)
        general_diff.set_column(3, 2, 25)

        bold = workbook.add_format({'bold': True})
        general_diff.write(general_diff_row, 0, TEST_NAME, bold)
        general_diff.write(general_diff_row, 1, FIRST, bold)
        general_diff.write(general_diff_row, 2, SECOND, bold)
        general_diff.write(general_diff_row, 3, DIFF, bold)

    dyn_inst_format = ''
    if first_dyn_inst_count - second_dyn_inst_count > 0:
        dyn_inst_format = workbook.add_format({'font_color': 'red'})

    general_diff_row += 1
    general_diff.write(general_diff_row, 0, bench_name, dyn_inst_format)
    general_diff.write(general_diff_row, 1, first_dyn_inst_count, dyn_inst_format)
    general_diff.write(general_diff_row, 2, second_dyn_inst_count, dyn_inst_format)
    general_diff.write(general_diff_row, 3, first_dyn_inst_count - second_dyn_inst_count, dyn_inst_format)


def get_files_from_dir(directory: str) -> List[str]:
    if os.path.isdir(directory):
        bbes = sorted(glob.glob(os.path.join(directory, "*.bbexec")))
        return bbes
    else:
        assert f"Cannot find directory: {directory}"


def get_bbe_files(args: Namespace) -> (List[str], List[str]):
    first_bbes = []
    second_bbes = []

    if args.first_bbes_dir:
        first_bbes = get_files_from_dir(args.first_bbes_dir)

    if args.second_bbes_dir:
        second_bbes = get_files_from_dir(args.second_bbes_dir)

    if args.first_bbe_file:
        assert (os.path.isfile(args.first_bbe_file)), \
            f"Cannot find first file: {args.first_bbe_file}"
        first_bbes = [args.first_bbe_file]

    if args.second_bbe_file:
        assert (os.path.isfile(args.second_bbe_file)), \
            f"Cannot find second file: {args.second_bbe_file}"
        second_bbes = [args.second_bbe_file]

    return first_bbes, second_bbes


def get_dyn_inst_count(file_path: str) -> int:
    with open(file_path, 'r') as f:
        f.seek(0, os.SEEK_END)
        fsize = f.tell()

        lines = []
        newline_chars = '\n\r'
        position = fsize - 1

        while len(lines) < 3 and position >= 0:
            f.seek(position)
            char = f.read(1)
            if char in newline_chars:
                lines.append(f.readline())
            position -= 1

        if lines[2]:
            return int(((lines[2]).split(':')[1]))


def compute_and_get_diff(first_bbe: str, second_bbe: str) -> Dict[str, List]:

    funcs_dyn_count_from_first_bbe = get_functions_dyn_inst_count(first_bbe)
    funcs_dyn_count_from_second_bbe = get_functions_dyn_inst_count(second_bbe)
    diff_result = get_cmp_result(funcs_dyn_count_from_first_bbe,
                                 funcs_dyn_count_from_second_bbe)

    return diff_result


def main():
    args = parse_args()
    first_bbes, second_bbes = get_bbe_files(args)

    if args.output_file:
        file_name = args.output_file
    else:
        file_name = os.path.join(CUR_DIR, XLSX_RESULT_FILE_NAME)

    workbook = xlsxwriter.Workbook(file_name)

    for idx, first_bbe in enumerate(first_bbes):
        second_bbe = None
        try:
            for bbe in second_bbes:
                if os.path.basename(bbe) == os.path.basename(first_bbe):
                    second_bbe = bbe
                    break

            if second_bbe:
                bench_name = os.path.basename((first_bbe.split(".bbexec"))[0])
                first_dyn_inst_count = get_dyn_inst_count(first_bbe)
                second_dyn_inst_count = get_dyn_inst_count(second_bbe)

                if (args.first_bbe_file and args.second_bbe_file) or args.create_functions_diff_sheet:
                    result = compute_and_get_diff(first_bbe, second_bbe)
                    create_diff_for_single_bbe(workbook, bench_name, result)

                if args.first_bbes_dir and args.second_bbes_dir:
                    create_general_diff(workbook, bench_name, first_dyn_inst_count,
                                        second_dyn_inst_count, idx)
            else:
                print(f"{first_bbe} file is not found.")
        except ValueError as ex:
            print(str(ex))

    workbook.close()


if __name__ == "__main__":
    main()
