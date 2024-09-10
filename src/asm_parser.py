# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

from src.instruction import Instruction
from typing import Dict


def add_labels(asm_code: Dict[str, Instruction]) -> Dict[str, Instruction]:
    count = 0
    instr_list = list(asm_code.values())
    length_of_lines = len(instr_list)

    for ind, source_instr in enumerate(instr_list):
        jump_target = source_instr.get_jump_target()
        if jump_target:
            jump_target = jump_target.lstrip("0x")
            if source_instr.code == 'jal':
                if ind + 1 < length_of_lines:
                    if not instr_list[ind + 1].get_label():
                        source_instr.set_jump_target(f"B{count}:")
                        instr_list[ind+1].set_label(f"B{count}:")
                        count += 1
                    else:
                        source_instr.set_jump_target(instr_list[ind + 1].get_label())

            jump_instr = asm_code.get(jump_target)
            if jump_instr:
                if jump_instr.get_label():
                    source_instr.set_jump_target(jump_instr.get_label())
                else:
                    new_label = f"B{count}:"
                    count += 1
                    jump_instr.set_label(new_label)
                    source_instr.set_jump_target(new_label)

                if ind + 1 < length_of_lines and not instr_list[ind + 1].get_label():
                    instr_list[ind+1].set_label(f"B{count}:")
                    count += 1
        if source_instr.is_ret():
            if ind + 1 < length_of_lines and not instr_list[ind + 1].get_label():
                instr_list[ind + 1].set_label(f"B{count}:")
                count += 1

    return asm_code


def normalize(asm_code: Dict[str, Instruction]) -> Dict[str, Instruction]:
    return add_labels(asm_code)


def parse_function_asm(lines: str) -> Dict[str, Instruction]:
    lines = lines.splitlines()
    asm_code = {}
    for line in lines:
        try:
            inst = Instruction(line)
        except Exception as e:
            print(f"Reached invalid instruction: {e}")
            continue
        asm_code[inst.get_address()] = inst

    asm_code = normalize(asm_code)

    return asm_code
