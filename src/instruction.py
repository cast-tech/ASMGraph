from src import opcodes
from enum import Enum


class Operand:
    class Code(Enum):
        REG = 1
        ADDRESS = 2
        CONSTANT = 3
        CALL = 4

    def __init__(self, code: Code, value: str):
        self.code = code
        self.value = value
        self.input = None
        self.output = []

    def as_int(self) -> int:
        assert self.code == self.Code.CONSTANT, f"Operand is not a constant [{self.value}]"
        num = 0
        try:
            num = int(self.value, 10)
        except ValueError:
            try:
                num = int(self.value, 16)
            except ValueError:
                assert False, f"Operand in wrong base {self.value}"

        return num

    def equal_to_number(self, number: int) -> bool:
        if self.code != self.code.CONSTANT:
            return False

        try:
            num = int(self.value, 10)
        except ValueError:
            try:
                num = int(self.value, 16)
            except ValueError:
                assert False, f"Operand in wrong base {self.value}"

        return num == number

    def __eq__(self, other) -> bool:
        if self.code != other.code:
            return False

        return self.value == other.value


class Instruction:
    def __init__(self, line):
        self.__content = line
        tmp_list = line.split()
        self.__address = tmp_list[0]
        self.__arguments = []
        self.__jump_target = None
        self.dest = None
        self.src1 = None
        self.src2 = None
        self.code = None

        if line[-1] == ":":
            self.__label = tmp_list[1]
            self.__is_branch = False
            self.__is_jump = False
            self.__is_ret = False
        else:
            self.__label = None
            self.code = tmp_list[1]
            if self.code not in opcodes.INSN_GROUP_DICT:
                msg = f"Wrong opcode: {self.code} ({line})"
                print(msg)
                raise ValueError(msg)

            self.__is_branch = self.code in opcodes.branch_instructions
            self.__is_jump = self.code in opcodes.jump_instructions
            self.__is_ret = self.code in opcodes.terminate

            if not self.__is_ret:
                assert len(tmp_list) > 2, f"Interesting case {line}"

                self.__arguments = tmp_list[2].split(',')
                self.dest = Operand(Operand.Code.REG, self.__arguments[0])

                if self.__is_jump or self.__is_branch:
                    self.__jump_target = tmp_list[2].split(",")[-1]
                    self.src1 = Operand(Operand.Code.ADDRESS, self.__jump_target)

                    if self.__jump_target[-1] != ":":
                        self.__jump_target = self.__jump_target + ":"

                    if self.code in opcodes.ternary_branch_instructions:
                        tmp_operand = self.src1
                        self.src1 = Operand(Operand.Code.REG, tmp_list[2].split(",")[-2])
                        self.src2 = tmp_operand
                else:
                    self.src1 = Operand(Operand.Code.REG, tmp_list[2].split(",")[-2])
                    arg = tmp_list[2].split(",")[-1]

                    if arg.startswith("0x"):
                        self.src2 = Operand(Operand.Code.CONSTANT, arg)
                    else:
                        try:
                            int(arg, 10)
                            self.src2 = Operand(Operand.Code.CONSTANT, arg)
                        except ValueError:
                            # It is register
                            self.src2 = Operand(Operand.Code.REG, arg)

                if self.code in opcodes.binary_instructions:
                    self.dest = self.src1
                    self.src1 = self.src2
                    self.src2 = None

    def is_ret(self):
        return self.__is_ret

    def is_jump(self):
        return self.__is_jump

    def is_branch(self):
        return self.__is_branch

    def is_store_to_stack(self, byte=8) -> bool:
        if self.code is None:
            return False

        if byte == 8:
            return self.code == "sd" and "sp" in self.src1.value
        elif byte == 4:
            return self.code == "sw" and "sp" in self.src1.value
        elif byte == 2:
            return self.code == "sh" and "sp" in self.src1.value
        elif byte == 1:
            return self.code == "sb" and "sp" in self.src1.value
        else:
            raise ValueError(f"Unsupported store instruction {self.code}")

    def get_arguments(self):
        return self.__arguments

    def get_address(self):
        return self.__address

    def get_address_int(self):
        return int(self.__address.strip(':'), 16)

    def get_jump_target(self):
        return self.__jump_target

    def get_label(self):
        return self.__label

    def get_dest_name(self) -> str:
        reg = self.dest.value
        return reg if "(" not in reg else reg[reg.index('(') + 1: reg.index(')')]

    def get_src1_name(self) -> str:
        reg = self.src1.value
        return reg if "(" not in reg else reg[reg.index('(') + 1: reg.index(')')]

    def get_src2_name(self) -> str:
        reg = self.src2.value
        return reg if "(" not in reg else reg[reg.index('(') + 1: reg.index(')')]

    def set_jump_target(self, target):
        self.__jump_target = target

    def set_label(self, label):
        self.__label = label

    def __str__(self):
        return self.__content
