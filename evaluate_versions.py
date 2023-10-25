#!/usr/bin/env python3

import os
import glob
import argparse
import xlsxwriter
from typing import Dict, List, NoReturn

FIRST = "FIRST"
SECOND = "SECOND"
FUNCTION_NAME = "FUNCTION NAME"
DYNAMIC_INST_COUNT = "DYN_COUNT"
BIT_INST_COUNT = "BIT_INST_COUNT"
TEST_NAME = "TEST NAME"
DYN_COUNT_DIFF = "DYN_COUNT_DIFF"

BITMANIP_INSTRUCTIONS = ['add.uw', 'andn', 'bclr', 'bclri', 'bext', 'bexti', 'binv', 'binvi',
                         'bset', 'bseti', 'clmul', 'clmulh', 'clmulr', 'clz', 'clzw', 'cpop',
                         'cpopw', 'ctz', 'ctzw', 'max', 'maxu', 'min', 'minu', 'orc.b', 'orn',
                         'rev8', 'rol', 'rolw', 'ror', 'rori', 'roriw', 'rorw', 'sext.b', 'sext.h',
                         'sh1add', 'sh1add.uw', 'sh2add', 'sh2add.uw', 'sh3add', 'sh3add.uw', 'slli.uw',
                         'xnor', 'zext.h']

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_RESULT_FILE_NAME = "evaluation_result.xlsx"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--first-collect-file', dest="first_collect_file", default=None,
                        help="Path to first hot block file")
    parser.add_argument('--second-collect-file', dest="second_collect_file", default=None,
                        help="Path to second hot block file")
    parser.add_argument('--first-collects-dir', dest="first_collects_dir", default=None,
                        help="Path to directory with first hot block files (with .collect files)")
    parser.add_argument('--second-collects-dir', dest="second_collects_dir", default=None,
                        help="Path to directory with second hot block files (with .collect files)")
    args = parser.parse_args()

    return args


def summary_blocks(collect_file: str, dyn_inst_count: int) -> [Dict[str, dict], int]:
    summary = {}

    with open(collect_file, "r") as block_fp:
        current_function_name = ''

        for line in block_fp:
            stripped_line = line.strip()
            if stripped_line.find("translation blocks") > 0 or \
                    stripped_line.find("(by dynamic instructions)") > 0:
                continue

            if stripped_line.find("by dynamic invocations") > 0:
                break

            if not stripped_line.startswith("0x"):
                block_info = stripped_line.split()
                if len(block_info) > 2:
                    if block_info[1] in BITMANIP_INSTRUCTIONS:
                        summary[current_function_name][BIT_INST_COUNT] += 1
                continue

            block_info = stripped_line.split()
            dyn_inst_count += int(block_info[1])

            if len(block_info) == 4:
                if "." in block_info[3]:
                    block_info[3] = block_info[3].split(".")[0]
                if block_info[3] in summary:
                    summary[block_info[3]][DYNAMIC_INST_COUNT] += int(block_info[1])
                else:
                    summary[block_info[3]] = {DYNAMIC_INST_COUNT: int(block_info[1]),
                                              BIT_INST_COUNT: 0}
                current_function_name = block_info[3]

    sort_by_exec_count = sorted(summary.items(), key=lambda x: x[1][DYNAMIC_INST_COUNT],
                                reverse=True)
    summary = dict(sort_by_exec_count)

    return summary, dyn_inst_count


def compare_blocks(origin_hot_blocks, cmp_hot_blocks) -> Dict[str, List]:
    result = {}
    for orig_func_name, orig_exec_count in origin_hot_blocks.items():
        same_cmp_block = [cmp_func_name for cmp_func_name, cmp_exec_count
                          in cmp_hot_blocks.items() if cmp_func_name == orig_func_name]

        if same_cmp_block:
            result[orig_func_name] = [orig_exec_count, cmp_hot_blocks[same_cmp_block[0]]]

    return result


def create_bench_hot_blocks_compare_sheet(workbook: xlsxwriter.Workbook,
                                          file_name: str,
                                          blocks: Dict[str, List]):
    bench_sheet = workbook.add_worksheet(file_name)
    row = 0
    col = 0
    bold = workbook.add_format({'bold': True})

    bench_sheet.set_column(0, 0, 25)
    bench_sheet.set_column(1, 1, 15)
    bench_sheet.set_column(2, 2, 15)
    bench_sheet.set_column(3, 2, 15)
    bench_sheet.set_column(4, 2, 15)
    bench_sheet.set_column(5, 2, 15)
    bench_sheet.set_column(6, 2, 15)
    bench_sheet.set_column(7, 2, 30)

    merge_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bold': True,
        'italic': True
    })

    bench_sheet.write(row, col, FUNCTION_NAME, merge_format)
    bench_sheet.write(row + 1, col + 1, DYNAMIC_INST_COUNT, bold)
    bench_sheet.merge_range('B1:C1', FIRST, merge_format)
    bench_sheet.write(row + 1, col + 2, BIT_INST_COUNT, bold)
    bench_sheet.write(row + 1, col + 3, DYNAMIC_INST_COUNT, bold)
    bench_sheet.merge_range('D1:E1', SECOND, merge_format)
    bench_sheet.write(row + 1, col + 4, BIT_INST_COUNT, bold)
    bench_sheet.merge_range('F1:G1', f"DIFFERENCE({FIRST} - {SECOND})", merge_format)
    bench_sheet.write(row + 1, col + 5, DYNAMIC_INST_COUNT, bold)
    bench_sheet.write(row + 1, col + 6, BIT_INST_COUNT, bold)
    bench_sheet.write(row, col + 7, f"DIFF(({FIRST} - {SECOND})/{SECOND}) %", merge_format)

    row += 2
    first_dyn_inst_count = 0
    second_dyn_inst_count = 0

    for item, cost in blocks.items():
        function_name_format = ''
        if cost[0][DYNAMIC_INST_COUNT] - cost[1][DYNAMIC_INST_COUNT] > 0 or \
                cost[0][BIT_INST_COUNT] - cost[1][BIT_INST_COUNT] < 0:
            function_name_format = workbook.add_format({'font_color': 'red'})

        bench_sheet.write(row, col + 1, cost[0][DYNAMIC_INST_COUNT])
        bench_sheet.write(row, col + 2, cost[0][BIT_INST_COUNT])
        first_dyn_inst_count += cost[0][DYNAMIC_INST_COUNT]

        bench_sheet.write(row, col + 3, cost[1][DYNAMIC_INST_COUNT])
        bench_sheet.write(row, col + 4, cost[1][BIT_INST_COUNT])
        second_dyn_inst_count += cost[1][DYNAMIC_INST_COUNT]

        dyn_inst_format = ''
        bitmanip_inst_format = ''
        if cost[0][DYNAMIC_INST_COUNT] - cost[1][DYNAMIC_INST_COUNT] > 0:
            dyn_inst_format = workbook.add_format({'font_color': 'red'})

        if cost[0][BIT_INST_COUNT] - cost[1][BIT_INST_COUNT] < 0:
            bitmanip_inst_format = workbook.add_format({'font_color': 'red'})

        bench_sheet.write(row, col, item, function_name_format)
        bench_sheet.write(row, col + 5, cost[0][DYNAMIC_INST_COUNT] - cost[1][DYNAMIC_INST_COUNT],
                          dyn_inst_format)
        bench_sheet.write(row, col + 6, cost[0][BIT_INST_COUNT] - cost[1][BIT_INST_COUNT],
                          bitmanip_inst_format)
        dynamic_inst_diff_percent = ((cost[0][DYNAMIC_INST_COUNT] - cost[1][DYNAMIC_INST_COUNT]) /
                                     cost[1][DYNAMIC_INST_COUNT]) * 100
        bench_sheet.write(row, col + 7, round(dynamic_inst_diff_percent, 2), dyn_inst_format)
        row += 1

    row += 2
    bench_sheet.write(row, col, "Sum_Dyn_Inst_Count", bold)
    bench_sheet.write(row, col + 1, first_dyn_inst_count, bold)
    bench_sheet.write(row, col + 3, second_dyn_inst_count, bold)
    bench_sheet.write(row, col + 5, first_dyn_inst_count - second_dyn_inst_count, bold)


def create_dyn_inst_count_cmp_sheet(workbook: xlsxwriter.Workbook,
                                    bench_name: str,
                                    first_dyn_inst_count: int,
                                    second_dyn_inst_count: int,
                                    general_diff_row: int) -> NoReturn:
    column = 0
    bold = workbook.add_format({'bold': True})
    general_diff = workbook.get_worksheet_by_name("general_diff")
    if not general_diff:
        general_diff = workbook.add_worksheet("general_diff")
        general_diff.set_column(0, 0, 25)
        general_diff.set_column(1, 1, 20)
        general_diff.set_column(2, 2, 25)
        general_diff.set_column(3, 2, 25)
        general_diff.write(general_diff_row, column, TEST_NAME, bold)
        general_diff.write(general_diff_row, column + 1, FIRST, bold)
        general_diff.write(general_diff_row, column + 2, SECOND, bold)
        general_diff.write(general_diff_row, column + 3, f"DIFFERENCE({FIRST} - {SECOND})", bold)

    dyn_inst_format = ''
    if first_dyn_inst_count - second_dyn_inst_count > 0:
        dyn_inst_format = workbook.add_format({'font_color': 'red'})

    general_diff.write(general_diff_row + 1, column, bench_name, dyn_inst_format)
    general_diff.write(general_diff_row + 1, column + 1, first_dyn_inst_count, dyn_inst_format)
    general_diff.write(general_diff_row + 1, column + 2, second_dyn_inst_count, dyn_inst_format)
    general_diff.write(general_diff_row + 1, column + 3, first_dyn_inst_count - second_dyn_inst_count,
                       dyn_inst_format)


def main():
    args = parse_args()
    first_collects = []
    second_collects = []

    if args.first_collects_dir:
        first_collects = glob.glob(os.path.join(args.first_collects_dir, "*.collect"))
        first_collects = sorted(first_collects)

    if args.second_collects_dir:
        second_collects = glob.glob(os.path.join(args.second_collects_dir, "*.collect"))
        second_collects = sorted(second_collects)

    if args.first_collect_file:
        first_collects = [args.first_collect_file]

    if args.second_collect_file:
        second_collects = [args.second_collect_file]

    if not first_collects:
        print("Can't find first hot block file(s)")
        return

    if not second_collects:
        print("Can't find second hot block file(s)")
        return

    first_dyn_inst_count = 0
    second_dyn_inst_count = 0

    # Create a workbook to compare two .collect files produced by two different compiler versions
    file_name = os.path.join(CUR_DIR, XLSX_RESULT_FILE_NAME)
    workbook = xlsxwriter.Workbook(file_name)
    for i in range(0, len(first_collects)):
        bench_name = os.path.basename((first_collects[i].split(".collect"))[0])

        first_blocks_inst_count, first_dyn_inst_count = summary_blocks(first_collects[i],
                                                                       first_dyn_inst_count)
        second_blocks_inst_count, second_dyn_inst_count = summary_blocks(second_collects[i],
                                                                         second_dyn_inst_count)
        diff_result = compare_blocks(first_blocks_inst_count, second_blocks_inst_count)
        create_bench_hot_blocks_compare_sheet(workbook, bench_name, diff_result)
        create_dyn_inst_count_cmp_sheet(workbook, bench_name, first_dyn_inst_count,
                                        second_dyn_inst_count, i)
        first_dyn_inst_count = 0
        second_dyn_inst_count = 0

    workbook.close()


if __name__ == "__main__":
    main()
