#!/usr/bin/env python3

# *******************************************************
# * Copyright (c) 2022-2023 CAST.  All rights reserved. *
# *******************************************************

import os
import argparse
from argparse import Namespace
import glob
import shutil
from typing import List, NoReturn

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECTS_DIR = os.path.join(CUR_DIR, "collects")

HAS_SIDE_BINARIES = {"525.x264_r": 3, "511.povray_r": 1, "521.wrf_r": 1,
                     "526.blender_r": 1, "527.cam4_r": 1, "538.imagick_r": 1}


def parse_arguments() -> Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-s", "--spec_dir", required=True, type=str,
                        help="Path to the compiler specCPU root.")

    parsed_args = parser.parse_args()
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


def get_primaries(collects: List[str], required_amount: int) -> List[str]:
    collects_exec_counts = {}
    necessary_collects = []

    for collect in collects:
        collects_exec_counts[collect] = get_dyn_inst_count(collect)

    sort_by_execution_count = sorted(collects_exec_counts.items(),
                                     key=lambda x: x[1], reverse=True)

    if len(sort_by_execution_count) >= required_amount:
        for idx, collect in enumerate(sort_by_execution_count):
            if idx < required_amount:
                necessary_collects.append(collect[0])
                continue

            break

    return necessary_collects


def copy_collect(CPU_DIR: str, out_dir: str) -> NoReturn:

  orig_collects = glob.glob(f"{CPU_DIR}/*/*/*.collect")

  benches = {}
  for c in orig_collects:
      bench_name = c.strip(CPU_DIR).split("/")[0]
      if bench_name in benches:
          benches[bench_name].append(c)
      else:
          benches[bench_name] = [c]

  for bench, collects in benches.items():

      if len(collects) != 1:
          if bench in HAS_SIDE_BINARIES.keys():
            collects = get_primaries(collects, HAS_SIDE_BINARIES[bench])
          i = 1
          for c in collects:
              shutil.copy(c, f"{out_dir}/{bench}_{i}.collect")
              i += 1
      else:
          shutil.copy(collects[0], f"{out_dir}/{bench}.collect")


def copy_exes(CPU_DIR: str, out_dir: str) -> NoReturn:
    for exe in glob.glob(f"{CPU_DIR}/*/exe"):
        shutil.copytree(exe, out_dir, dirs_exist_ok=True)


def main(args: Namespace):
    args = parse_arguments()
    spec_cpu_dir = os.path.join(args.spec_dir, "benchspec", "CPU")
    assert os.path.exists(spec_cpu_dir), f"Cant find directory '{spec_cpu_dir}'"

    if os.path.exists(COLLECTS_DIR):
        shutil.rmtree(COLLECTS_DIR, ignore_errors=True)

    os.mkdir(COLLECTS_DIR)
    copy_collect(spec_cpu_dir, COLLECTS_DIR)
    copy_exes(spec_cpu_dir, COLLECTS_DIR)


if __name__ == '__main__':
    main(parse_arguments())

