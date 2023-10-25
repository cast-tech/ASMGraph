# *******************************************************
# * Copyright (c) 2022-2023 CAST.  All rights reserved. *
# *******************************************************

# This file tends to check instruction fusion on BB.
# Each checker should get as an argument BB and should return (Instr_1, Instr_2) when BB is eligible and None otherwise.

import re
from typing import List, NoReturn
from .graph import Node
from .opcodes import loads, stores, jump_instructions
from .instruction import Instruction, Operand


def check_extend(basic_block: Node, n: int) -> List[dict]:
    fusion_data = []
    for first_inst in basic_block:
        if first_inst.code in ["slli", "sll"] and first_inst.src2.equal_to_number(n):
            for used_in in first_inst.dest.output:
                if used_in.code in ["srli", "srl"] and used_in.src2.equal_to_number(n) and \
                        are_destinations_same(first_inst, used_in):
                    a = first_inst.get_address_int()
                    b = used_in.get_address_int()
                    if b - a > 4 and instructions_are_far(basic_block, first_inst, used_in):
                        fusion_data.append({first_inst: used_in})

    return fusion_data


def check_semi_extend_si_di(basic_block: Node, n: int) -> List[dict]:
    fusion_data = []
    for first_inst in basic_block:
        if first_inst.code in ["slli", "sll"] and first_inst.src2.equal_to_number(n):
            for used_in in first_inst.dest.output:
                if used_in.code in ["srli", "srl"] and used_in.src2.as_int() <= n and \
                        are_destinations_same(first_inst, used_in):
                    a = first_inst.get_address_int()
                    b = used_in.get_address_int()
                    if b - a > 4 and instructions_are_far(basic_block, first_inst, used_in):
                        fusion_data.append({first_inst: used_in})

    return fusion_data


def check_integer_indexed_loads(basic_block: Node) -> List[dict]:
    fusion_data = []
    for first_inst in basic_block:
        if first_inst.code == "add":
            dst_of_first_instr_used_in_load(basic_block, first_inst, fusion_data)

    return fusion_data


def check_load_with_preincrement(basic_block: Node) -> List[dict]:
    fusion_data = []
    for first_inst in basic_block:
        if first_inst.code == "addi":
            dst_of_first_instr_used_in_load(basic_block, first_inst, fusion_data)

    return fusion_data


def check_load_from_const_address(basic_block: Node) -> List[dict]:
    fusion_data = []
    for first_inst in basic_block:
        if first_inst.code == "auipc" or first_inst.code == "lui":
            dst_of_first_instr_used_in_load(basic_block, first_inst, fusion_data)

    return fusion_data


def check_address_and_const_formation(basic_block: Node) -> List[dict]:
    fusion_data = []
    for first_inst in basic_block:
        if first_inst.code in ["lui", "auipc"]:
            for used_in in first_inst.dest.output:
                if used_in.code in ["addi", "add"] and \
                        used_in.src2.code == Operand.Code.CONSTANT and \
                        are_destinations_same(first_inst, used_in):
                    a = first_inst.get_address_int()
                    b = used_in.get_address_int()
                    if b - a > 4 and instructions_are_far(basic_block, first_inst, used_in):
                        fusion_data.append({first_inst: used_in})

    return fusion_data


def check_double_constant_formation(basic_block: Node) -> List[dict]:
    fusion_data = []
    input_key = None
    input_inst = None
    for first_inst in basic_block:
        if first_inst.code == "lui":
            for used_in in first_inst.dest.output:
                if used_in.code in ["addi", "add"] and \
                        used_in.src2.code == Operand.Code.CONSTANT and \
                        are_destinations_same(first_inst, used_in):

                    input_ind = basic_block.get_instr_list().index(first_inst)
                    out_ind = basic_block.get_instr_list().index(used_in)
                    if out_ind - input_ind == 1:
                        if input_key and not are_destinations_same(input_inst, first_inst):
                            fusion_data.append({input_key: f"{first_inst}\n{used_in}\n"})
                        input_inst = first_inst
                        input_key = f"{first_inst}\n{used_in}\n---------\n"

    return fusion_data


def check_lui_add_shnadd_ld(basic_block: Node) -> List[dict]:
    fusion_data = []
    for first_inst in basic_block:
        if first_inst.code == "lui":
            for used_in in first_inst.dest.output:
                if used_in.code in ["addi", "add"] and \
                        used_in.src2.code == Operand.Code.CONSTANT and \
                        are_destinations_same(first_inst, used_in):

                    for second in used_in.dest.output:
                        if second.code in ["sh1add", "sh2add", "sh3add"]:
                            for second_used in second.dest.output:
                                if second_used.code == "ld":
                                    fusion_data.append({f"{first_inst}\n{used_in}":
                                                        f"{second}\n{second_used}"})

    return fusion_data


def check_two_stores(basic_block: Node) -> List[dict]:
    fusion_data = []
    instr_count = len(basic_block)
    for i in range(instr_count):
        first_sd = basic_block[i]
        if first_sd.is_store_to_stack():
            first_offset = get_offset(first_sd.src1)
            if first_offset % 16 == 0:
                for j in range(i + 1, instr_count):
                    second_sd = basic_block[j]
                    if second_sd.is_store_to_stack():
                        second_offset = get_offset(second_sd.src1)
                        if first_offset + 8 == second_offset:

                            changed_in_pos = is_changed_in_range(basic_block, i, j,
                                                                 second_sd.dest)
                            if changed_in_pos == 0:
                                a = first_sd.get_address_int()
                                b = second_sd.get_address_int()
                                if b - a > 2 and instructions_are_far(basic_block, first_sd, second_sd):
                                    fusion_data.append({first_sd: second_sd})

                                '''
                                    Discard those cases too
                                        sd a1, 0(sp)
                                        OP a1, x, y
                                        sd a1, 8(sp)
                                '''
                            elif basic_block[changed_in_pos].dest != first_sd.dest:

                                # Check whether first_sd can be moved between change and second_sd
                                # It is simple check, and we are not guarantee possibility
                                chang_instr_input = basic_block[changed_in_pos].dest.input
                                first_sd_address = first_sd.get_address_int()

                                if chang_instr_input is None or \
                                        chang_instr_input.get_address_int() < first_sd_address:
                                    fusion_data.append({first_sd: second_sd})

    return fusion_data


def dst_of_first_instr_used_in_load(basic_block: Node, first_instr: Instruction,
                                    fusion_data: List[dict]) -> NoReturn:
    for used_in in first_instr.dest.output:
        if used_in.code == "ld" and offset_is_zero(used_in.src1.value):
            a = first_instr.get_address_int()
            b = used_in.get_address_int()
            if b - a > 4 and instructions_are_far(basic_block, first_instr, used_in):
                fusion_data.append({first_instr: used_in})


def are_destinations_same(input_ins: Instruction, output_ins: Instruction) -> bool:
    return input_ins.dest == output_ins.dest


def get_offset(reg: Operand) -> int:
    assert type(reg) is Operand, "Wrong usage of function"

    address = reg.value
    addr = address.split("(")
    if not addr:
        raise ValueError(f"Wrong format of address {address}")

    addr = addr[0]
    try:
        return int(addr, 10)
    except ValueError:
        try:
            return int(addr, 16)
        except ValueError:
            raise ValueError(f"Address is in wrong format {address}")


def offset_is_zero(address: str) -> bool:
    pattern = r"^0\b"
    match = re.search(pattern, address)
    if match:
        return True
    return False


def instructions_are_far(basic_block: Node, first_ins: Instruction,
                         used_ins: Instruction) -> bool:
    instructions = basic_block.get_instr_list()
    input_ind = instructions.index(first_ins)
    out_ind = instructions.index(used_ins)
    count = 0

    for i in range(input_ind + 1, out_ind):
        if basic_block[i].code in jump_instructions:
            return False

        if basic_block[i].src1:
            if basic_block[i].code in loads or basic_block[i].code in stores:

                # extract register name from address operand. e.g 8(a2) -> a2
                src1 = get_register_from_address(basic_block[i].src1.value)

                if first_ins.dest.value == src1:
                    count += 1

            if first_ins.dest == basic_block[i].src1:
                count += 1
                continue

        if basic_block[i].src2:
            if first_ins.dest == basic_block[i].src2:
                count += 1

    return count < (out_ind - input_ind - 1)


#  This function checks whether 'reg' changed in the range of [i, j]
#  Returns 0 if not changed and the position it is done.
def is_changed_in_range(basic_block: Node, begin: int, end: int, reg: Operand) -> int:
    for i in range(begin, end):
        instr = basic_block[i]
        if instr.code in stores:
            continue

        if instr.dest == reg:
            return i

    return 0


def get_register_from_address(address: str) -> str:
    # Regular expression pattern to match the substring inside parentheses
    pattern = r'\((.*?)\)'
    # Search for the pattern in the text
    result = re.search(pattern, address)
    if result:
        # Extract the substring inside parentheses
        return result.group(1)
    raise ValueError(f"Cannot extract register name from {address}.")


def is_store_to_stack(address: str) -> bool:
    return get_register_from_address(address) == "sp"


def process_basic_block(basic_block: Node, function_name: str, xlsx_for_fusions) -> NoReturn:

    fuse = check_extend(basic_block, 48)
    if fuse:
        title = "Extend HI to DI"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_extend(basic_block, 32)
    if fuse:
        title = "Extend SI to DI"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_semi_extend_si_di(basic_block, 32)
    if fuse:
        title = "Semi extend SI to DI (less than 32)"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_integer_indexed_loads(basic_block)
    if fuse:
        title = "Integer indexed loads"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_load_with_preincrement(basic_block)
    if fuse:
        title = "Load with preincrement"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_load_from_const_address(basic_block)
    if fuse:
        title = "Loads from constant addresses"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_address_and_const_formation(basic_block)
    if fuse:
        title = "Address and constant formation"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_double_constant_formation(basic_block)
    if fuse:
        title = "Double address and constant formation"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_lui_add_shnadd_ld(basic_block)
    if fuse:
        title = "lui + add + shNadd + ld"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse)

    fuse = check_two_stores(basic_block)
    if fuse:
        title = "Two stores"
        xlsx_for_fusions.append_checker_result(title, function_name, basic_block, fuse, True)
