import src.opcodes


class ValueDict(dict):
    def __init__(self):
        super().__init__()

    def add(self, key, value):
        if key in self.keys():
            value = value + self.get(key)
            self.update({key: value})
        else:
            self[key] = value


def get_bb_address(addr):
    tmp_addr = int(addr, 16)
    if tmp_addr >= int("0x4000000000", 16):
        return hex(tmp_addr - 0x4000000000).lstrip("0x")
    else:
        return hex(tmp_addr).lstrip("0x")


class CollectFileParser:
    def __init__(self, file_name):
        self.__file_name = file_name
        with open(self.__file_name, "r") as col_file:
            self.__content = col_file.readlines()

        if not self.__content:
            print("Cannot get data from collect file!")
        self.__content = [line.strip() for line in self.__content if line.strip()]

        self.__bb_usage_info = {}

        self.__total_exec_count = 0
        self.__inst_group_dict = ValueDict()

    def parse_collect_file(self):
        per_inst_exec_count = 0
        dyn_instr_block_section = False

        # TODO: optimize it later
        for i, line in enumerate(self.__content):
            if not dyn_instr_block_section:
                if line == "## Blocks (by dynamic instructions)":
                    dyn_instr_block_section = True
                continue

            if line == "## Blocks (by dynamic invocations)":
                break

            if line.startswith("0x"):
                tmp_list = line.split()
                exec_count = int(tmp_list[1])
                self.__total_exec_count += exec_count

                bb_addr = get_bb_address(tmp_list[0]) + ":"
                self.__bb_usage_info[bb_addr] = exec_count

                instr_lines_count = 0
                if i + 1 < len(self.__content):
                    for ind in range(i + 1, len(self.__content)):
                        if not self.__content[ind] or self.__content[ind].startswith("0x") or \
                                self.__content[ind] == "## Blocks (by dynamic invocations)":
                            break
                        instr_lines_count += 1
                    per_inst_exec_count = exec_count / instr_lines_count
            else:
                inst = line.split()[1]
                self.__inst_group_dict.add(src.opcodes.INSN_GROUP_DICT[inst], per_inst_exec_count)

    def extract_usage_info(self, addresses):
        if not self.__bb_usage_info:
            return {}

        usage_info = {}
        for addr in addresses:
            if addr in self.__bb_usage_info:
                usage_info[addr] = self.__bb_usage_info[addr]

        return usage_info

    def print_info_from_collect(self):
        print(f"Total Instructions: {self.__total_exec_count:,}")
        print('Instruction Groups:')
        for k, v in sorted(self.__inst_group_dict.items(), key=lambda item: item[1], reverse=True):
            print(k.rjust(18), f"{v:,}")
