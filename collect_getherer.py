#!/usr/bin/env python3

# *******************************************************
# * Copyright (c) 2022-2023 CAST.  All rights reserved. *
# *******************************************************

import os
import glob
import shutil

COLLECTS_DIR = "./collects"


def copy_collect(CPU_DIR, out_dir):

  orig_collects = glob.glob(f"{CPU_DIR}/*/*/*/*.collect")

  benches = {}
  for c in orig_collects:
      bench_name = c.strip(CPU_DIR).split("/")[0]
      if bench_name in benches:
          benches[bench_name].append(c)
      else:
          benches[bench_name] = [c]


  for bench, collects in benches.items():
 
      if len(collects) != 1:
          i = 1
          for c in collects:
              shutil.copy(c, f"{out_dir}/{bench}_{i}.collect")
              i += 1
      else:
          shutil.copy(collects[0], f"{out_dir}/{bench}.collect")


def copy_exes(CPU_DIR, out_dir):
    for exe in glob.glob(f"{CPU_DIR}/*/exe"):
        shutil.copytree(exe, out_dir, dirs_exist_ok=True)

os.mkdir(COLLECTS_DIR)
copy_collect("./benchspec/CPU", COLLECTS_DIR)
copy_exes("./benchspec/CPU", COLLECTS_DIR)

