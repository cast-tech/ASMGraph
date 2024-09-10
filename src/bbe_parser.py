# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import json
import os.path
from collections import defaultdict

from typing import List, Dict, NoReturn

BLOCKS_SEGMENT_START = "### Hot Blocks"
BLOCKS_SEGMENT_END = "### Overall Statistics"
TOTAL_DYN_INST = 'total_dyn_inst_count'

class ValueDict(dict):
    def __init__(self):
        super().__init__()

    def add(self, key: str, value: float) -> NoReturn:
        if key in self.keys():
            value = value + self.get(key)
            self.update({key: value})
        else:
            self[key] = value


def get_bb_address(addr: str) -> str:
    tmp_addr = int(addr, 16)
    if tmp_addr >= int("0x555555556000", 16):
        return hex(tmp_addr - 0x555555556000).lstrip("0x")
    if tmp_addr >= int("0x4000000000", 16):
        return hex(tmp_addr - 0x4000000000).lstrip("0x")

    return hex(tmp_addr).lstrip("0x")


class BBEFileParser:
    def __init__(self, project_dir: str):
        self.__files_names = []
        self.bbe_info_file = os.path.join(project_dir, "bbe_info.json")
        self.__total_exec_count = 0
        self.__total_dyn_inst_count = 0

    def __process_blocks_segment(self, file_name, process_func) -> None:
        with open(file_name, "r") as bbe:
            for line in bbe:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("0x"):
                    process_func(line)
                    continue

                if "Total Dynamic Instructions" in line:
                    self.__total_dyn_inst_count += int(line.split(':')[-1])



    def parse_and_save_data(self, files: List[str]):
        self.__files_names = files
        content = {}

        def extract_data(line):
            line_s = line.split()
            bb_address = get_bb_address(line_s[0]) + ":"
            exec_count = int(line_s[1])
            func_name = line_s[3] if 3 < len(line_s) else "-"

            if bb_address in content:
                content[bb_address]["execution_count"] += exec_count
                if func_name != "-" and content[bb_address]["function"] == "-":
                    content[bb_address]["function"] = func_name
            else:
                content[bb_address] = {"execution_count": exec_count, "function": func_name}

            self.__total_exec_count += exec_count

        for file_name in self.__files_names:
            if not os.path.isfile(file_name):
                print(f"Cannot find such .bbexec file {file_name}")
                continue

            self.__process_blocks_segment(file_name, extract_data)

        content[TOTAL_DYN_INST] = self.__total_dyn_inst_count

        with open(self.bbe_info_file, "w") as bbe_info:
            json.dump(content, bbe_info, indent=4)

    def extract_usage_info(self, addresses: List) -> Dict[str, int]:
        if not os.path.isfile(self.bbe_info_file):
            return {}

        usage_info = {}

        with open(self.bbe_info_file, "r") as bbe_info:
            data = json.load(bbe_info)

            for address in addresses:
                info = data.get(address)
                if info:
                    usage_info[address] = info.get("execution_count", 0)

        return usage_info

    def extract_total_exec_info_for_each_func(self):
        if not os.path.isfile(self.bbe_info_file):
            return None

        total_exec_by_func = defaultdict(int)

        with open(self.bbe_info_file, "r") as bbe_info:
            data = json.load(bbe_info)
            for addr, info in data.items():
                if addr == TOTAL_DYN_INST:
                    total_exec_by_func[TOTAL_DYN_INST] = info
                    continue

                if info.get("function") == "-":
                    continue

                total_exec_by_func[info["function"]] += info.get("execution_count", 0)

        return total_exec_by_func

    def print_info(self) -> NoReturn:

        print(f"Total Instructions: {self.__total_exec_count:,}")
        print('Instruction Groups:')
        for k, v in sorted(self.__inst_group_dict.items(), key=lambda item: item[1], reverse=True):
            print(k.rjust(18), f"{v:,}")
