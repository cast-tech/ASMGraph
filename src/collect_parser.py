# *******************************************************
# * Copyright (c) 2022-2023 CAST.  All rights reserved. *
# *******************************************************

import src.opcodes
from typing import List, Dict, NoReturn


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
    if tmp_addr >= int("0x4000000000", 16):
        return hex(tmp_addr - 0x4000000000).lstrip("0x")
    else:
        return hex(tmp_addr).lstrip("0x")


class CollectFileParser:
    def __init__(self, file_name: str):
        self.__file_name = file_name
        with open(self.__file_name, "r") as col_file:
            self.__content = col_file.readlines()

        if not self.__content:
            print("Cannot get data from collect file!")
        self.__content = [line.strip() for line in self.__content if line.strip()]

        self.__bb_usage_info = {}

        self.__total_exec_count = 0
        self.__inst_group_dict = ValueDict()

    def parse_collect_file(self, target_func: Dict[str, str]) -> NoReturn:
        per_inst_exec_count = 0
        dyn_instr_block_section = False
        func_name = None

        for ind, name in enumerate(target_func.items()):
            func_name = name[ind]
        for i, line in enumerate(self.__content):
            if not dyn_instr_block_section:
                if line == "## Blocks (by dynamic instructions)":
                    dyn_instr_block_section = True
                continue

            if line == "## Blocks (by dynamic invocations)":
                break
            inst = line.split()[1]
            if line.startswith("0x") and line.endswith(func_name):
                tmp_list = line.split()
                bb_addr = get_bb_address(tmp_list[0]) + ":"
                exec_count = int(tmp_list[1])
                self.__total_exec_count += exec_count
                self.__bb_usage_info[bb_addr] = exec_count

                instr_lines_count = 0
                for ind, next_line in enumerate(self.__content[i + 1:], start=i + 1):
                    if not next_line or next_line.startswith("0x") or next_line == "## Blocks (by dynamic invocations)":
                        break
                    instr_lines_count += 1
                per_inst_exec_count = exec_count / instr_lines_count

            elif inst in src.opcodes.INSN_GROUP_DICT:
               self.__inst_group_dict.add(src.opcodes.INSN_GROUP_DICT[inst], per_inst_exec_count)

    def extract_usage_info(self, addresses: List) -> Dict[str, int]:

        if not self.__bb_usage_info:
            return {}

        usage_info = {}
        for addr in addresses:
            if addr in self.__bb_usage_info:
                usage_info[addr] = self.__bb_usage_info[addr]

        return usage_info

    def print_info_from_collect(self) -> NoReturn:

        print(f"Total Instructions: {self.__total_exec_count:,}")
        print('Instruction Groups:')
        for k, v in sorted(self.__inst_group_dict.items(), key=lambda item: item[1], reverse=True):
            print(k.rjust(18), f"{v:,}")
