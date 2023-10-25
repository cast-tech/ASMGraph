#!/usr/bin/env python3

# *******************************************************
# * Copyright (c) 2022-2023 CAST.  All rights reserved. *
# *******************************************************


import os
import glob
import argparse
import xlsxwriter

FIRST = "FIRST"
SECOND = "SECOND"
FUNCTION_NAME = "FUNCTION NAME"
DIFF = "DIFF (FIRST - SECOND)"
DIFF_IN_PERCENTS = "DIFF IN PERCENTS"
TOTAL = "TOTAL"
DYNAMIC_INST_COUNT = "DYN_COUNT"
TEST_NAME = "TEST NAME"
DYN_COUNT_DIFF = "DYN_COUNT_DIFF"

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


def summary_blocks(collect_file):
    summary = {}
    dyn_inst_count = 0

    with open(collect_file, "r") as block_fp:

        for line in block_fp:
            line = line.strip()
            if "translation blocks" in line or "(by dynamic instructions)" in line:
                continue

            if "by dynamic invocations" in line:
                break

            if not line.startswith("0x"):
                continue

            block_info = line.split()
            dyn_inst_count += int(block_info[1])

            if len(block_info) == 4:
                function_name = block_info[3]
                if "." in function_name:
                    function_name = function_name.split(".")[0]

                if function_name in summary:
                    summary[function_name] += int(block_info[1])
                else:
                    summary[function_name] = int(block_info[1])

    sort_by_exec_count = sorted(summary.items(), key=lambda x: x[1], reverse=True)
    summary = dict(sort_by_exec_count)

    return summary, dyn_inst_count


def compare_blocks(origin_hot_blocks, cmp_hot_blocks):
    result = {}
    for orig_func_name, orig_exec_count in origin_hot_blocks.items():
        same_cmp_block = cmp_hot_blocks[orig_func_name]

        if same_cmp_block:
            result[orig_func_name] = [orig_exec_count, same_cmp_block]

    return result


def prepare_header(workbook, sheet_name):
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


def create_diff_for_single_collect(workbook, file_name, blocks):

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


def create_general_diff(workbook, bench_name, first_dyn_inst_count, second_dyn_inst_count, general_diff_row):

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

    file_name = os.path.join(CUR_DIR, XLSX_RESULT_FILE_NAME)
    workbook = xlsxwriter.Workbook(file_name)
    for i in range(0, len(first_collects)):
        bench_name = os.path.basename((first_collects[i].split(".collect"))[0])

        first_blocks_inst_count, first_dyn_inst_count = summary_blocks(first_collects[i])
        second_blocks_inst_count, second_dyn_inst_count = summary_blocks(second_collects[i])

        diff_result = compare_blocks(first_blocks_inst_count, second_blocks_inst_count)
        create_diff_for_single_collect(workbook, bench_name, diff_result)

        create_general_diff(workbook, bench_name, first_dyn_inst_count, second_dyn_inst_count, i)

    workbook.close()


if __name__ == "__main__":
    main()
