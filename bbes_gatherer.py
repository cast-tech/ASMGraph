#!/usr/bin/env python3

# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import os
import argparse
from argparse import Namespace
import glob
import shutil
from importlib.metadata import files
from typing import List, NoReturn

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
BBE_DIR = os.path.join(CUR_DIR, "bbexecs")

HAS_SIDE_BINARIES = {"525.x264_r": 3, "511.povray_r": 1, "521.wrf_r": 1,
                     "526.blender_r": 1, "527.cam4_r": 1, "538.imagick_r": 1}


def parse_arguments() -> Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-s", "--spec_dir", required=True, type=str,
                        help="Path to SPEC root.")
    parser.add_argument("-b", "--base", action="store_true",
                        help=f"Collect only base.")
    parser.add_argument("-p", "--pick", action="store_true",
                        help=f"Collect only pick.")
    parser.add_argument("-o", "--output", type=str, default=BBE_DIR,
                        help=f"The name of the out directory. (by default: {BBE_DIR})")

    parsed_args = parser.parse_args()

    if not parsed_args.base and not parsed_args.pick:
        parser.error('At least one of the "--base" and "--pick" must be specified.')

    return parsed_args


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
            return int(lines[2].split(':')[1])


def get_primaries(bbexecs: List[str], required_amount: int) -> List[str]:
    bbexec_counts = {}
    necessary_bbexecs = []

    for bbe in bbexecs:
        bbexec_counts[bbe] = get_dyn_inst_count(bbe)

    sort_by_execution_count = sorted(bbexec_counts.items(),
                                     key=lambda x: x[1], reverse=True)

    if len(sort_by_execution_count) >= required_amount:
        for idx, bbexec in enumerate(sort_by_execution_count):
            if idx < required_amount:
                necessary_bbexecs.append(bbexec[0])
                continue

            break

    return necessary_bbexecs


def copy_bbexec(CPU_DIR: str, out_dir: str, base: bool, pick: bool) -> NoReturn:
    bbexecs = glob.glob(f"{CPU_DIR}/*/*/*/*.bbexec")

    benches = {}

    def add_bench(bench_n, bbe):
        if bench_n in benches:
            benches[bench_n].append(bbe)
        else:
            benches[bench_n] = [bbe]

    for bbe in bbexecs:
        bench_name = bbe.strip(CPU_DIR).split("/")[0]
        bench_path = os.path.join(CPU_DIR, bench_name)

        if base and pick:
            add_bench(bench_name, bbe)
        elif base and glob.glob(f"{bench_path}/exe/*base*"):
            add_bench(bench_name, bbe)
        elif pick and glob.glob(f"{bench_path}/exe/*pick*"):
            add_bench(bench_name, bbe)

    for bench, bbexecs in benches.items():
        os.mkdir(f"{out_dir}/{bench}")
        if len(bbexecs) != 1:
            if bench in HAS_SIDE_BINARIES.keys():
                bbexecs = get_primaries(bbexecs, HAS_SIDE_BINARIES[bench])
            i = 1
            for c in bbexecs:
                shutil.copy(c, f"{out_dir}/{bench}/{i}.bbexec")
                i += 1
        else:
            shutil.copy(bbexecs[0], f"{out_dir}/{bench}/1.bbexec")

def copy_exes(cpu_dir: str, out_dir: str, base: bool, pick: bool) -> NoReturn:
    pattern = []
    if base:
        pattern.append(f"{cpu_dir}/*/exe/*base*")
    if pick:
        pattern.append(f"{cpu_dir}/*/exe/*pick*")

    if not pattern:
        return

    for pattern in pattern:
        for exe in glob.glob(pattern):
            file_name = os.path.basename(exe)
            if file_name.startswith("ldecod") or file_name.startswith("imagevalidate"):
                continue

            bench = exe.split("/")[-3]
            shutil.copy(exe, os.path.join(out_dir, bench, os.path.basename(exe)))

def main(args: Namespace):
    global BBE_DIR
    BBE_DIR = args.output

    args = parse_arguments()
    spec_cpu_dir = os.path.join(args.spec_dir, "benchspec", "CPU")
    assert os.path.isdir(spec_cpu_dir), f"Cant find directory '{spec_cpu_dir}'"

    if os.path.exists(BBE_DIR):
        shutil.rmtree(BBE_DIR, ignore_errors=True)

    os.mkdir(BBE_DIR)
    copy_bbexec(spec_cpu_dir, BBE_DIR, args.base, args.pick)
    copy_exes(spec_cpu_dir, BBE_DIR, args.base, args.pick)



if __name__ == '__main__':
    main(parse_arguments())
