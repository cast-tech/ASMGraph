#!/usr/bin/env python3

import os
import argparse
from argparse import Namespace
import glob
import shutil
from typing import List, NoReturn

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECTS_DIR = os.path.join(CUR_DIR, "collects")

EXCLUDE_LIST = ["525.x264_r", "511.povray_r", "521.wrf_r",
                "526.blender_r", "527.cam4_r", "538.imagick_r"]


def parse_arguments() -> Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-s", "--spec_dir", required=True, type=str,
                        help="Path to the compiler specCPU root.")

    parsed_args = parser.parse_args()
    return parsed_args


def get_dyn_inst_count(file_path: str) -> int:
    with open(file_path, 'r') as f:
        f.seek(0, 2)
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

        if lines[::-1][0]:
            return int(((lines[::-1][0]).split(':')[1]))


def delete_needless_collects(collects: List) -> List[str]:
    collects_exec_counts = {}
    necessary_collects = []

    for collect in collects:
        exec_count = get_dyn_inst_count(collect)
        collects_exec_counts[collect] = exec_count

    filtered_collects = sorted(collects_exec_counts.items(),
                               key=lambda x: x[1], reverse=True)

    if len(filtered_collects) >= 3:
        necessary_collects.append(filtered_collects[0][0])
        necessary_collects.append(filtered_collects[1][0])
        necessary_collects.append(filtered_collects[2][0])

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
          if bench in EXCLUDE_LIST:
            collects = delete_needless_collects(collects)
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

