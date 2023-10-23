import signal

import pydot
from typing import List
from .opcodes import loads, stores, branch_instructions, jump_instructions
from .instruction import Instruction


class Node:
    def __init__(self, label, start_address, instruction_list: List[Instruction]):
        # need for iteration
        self.__index = 0
        self.__label = label
        self.__instr_list = list(instruction_list)
        self.create_dataflow_graph()

        self.__start_address = start_address.lstrip("0")
        if self.__start_address[-1] != ":":
            self.__start_address += ":"

        self.__content = ""
        for instr in self.__instr_list:
            self.__content += str(instr) + "\l\t"
        self.txt = self.__content

        self.__jump_target = instruction_list[-1].get_jump_target()
        self.__branch_inst = instruction_list[-1].is_branch()
        self.__jump_inst = instruction_list[-1].is_jump()
        self.__ret_inst = instruction_list[-1].is_ret()

        self.__execution_count = None
        self.__color = None

        self.is_singleton = False

        self.__dot_Node = None

    def create_dataflow_graph(self):
        for selected_ins_ind in range(0, len(self.__instr_list)):

            if self.__instr_list[selected_ins_ind].is_ret() or \
                    self.__instr_list[selected_ins_ind].get_arguments() == []:
                continue

            self.search_dependencies(selected_ins_ind)

    def search_dependencies(self, selected_ins_ind):
        for current_ind in range(selected_ins_ind + 1, len(self.__instr_list)):
            if not self.__instr_list[current_ind].dest:
                continue

            if self.make_deps(selected_ins_ind, current_ind):
                break

    def make_deps(self, selected_ins_ind, next_ins_ind):
        selected_ins = self.__instr_list[selected_ins_ind]
        next_ins = self.__instr_list[next_ins_ind]

        if next_ins.code in stores:
            if selected_ins.dest.value == next_ins.get_dest_name():
                selected_ins.dest.output.append(next_ins)
                next_ins.dest.input = selected_ins

        if next_ins.src1:
            if selected_ins.dest.value == next_ins.get_src1_name():
                selected_ins.dest.output.append(next_ins)
                next_ins.src1.input = selected_ins

                if selected_ins.dest == next_ins.dest:
                    return True

        if next_ins.src2:
            if selected_ins.dest.value == next_ins.get_src2_name():
                selected_ins.dest.output.append(next_ins)
                next_ins.src2.input = selected_ins

                if selected_ins.dest == next_ins.dest:
                    return True

        return False

    def get_label(self):
        return self.__label

    def get_instr_list(self) -> List[Instruction]:
        return self.__instr_list

    def get_address(self):
        return self.__start_address

    def get_inner_content(self):
        return self.__content

    def ends_with_ret_inst(self):
        return self.__ret_inst

    def ends_with_br_inst(self):
        return self.__branch_inst

    def get_jump_target(self):
        return self.__jump_target

    def set_usage_info(self, usage_info):
        self.__execution_count = usage_info

    def get_execution_count(self):
        return self.__execution_count

    def set_color(self, color):
        self.__color = color

    def has_singleton_inst(self):
        if len(self.__instr_list) == 1:
            opcode = self.get_inner_content().split()[1]
            jumps = jump_instructions + ['ret\\l', 'ret\l', 'ret\l\t']
            unnecessary_opcodes = loads + stores + jumps + branch_instructions

            if opcode not in unnecessary_opcodes:
                return True
        return False

    def create_dot_node(self):
        if self.__execution_count:
            content = f"{self.__label} # usage info: {self.__execution_count}\l\t{self.__content}\l"
            if self.is_singleton:
                self.__dot_Node = pydot.Node(self.__label, label=content, margin="0.3",
                                             style="filled", shape="rect", color="limegreen")
            elif self.__execution_count == "empty":
                self.__dot_Node = pydot.Node(self.__label, label=content, margin="0.3",
                                             style="filled", shape="rect", color="steelblue")
            else:
                self.__dot_Node = pydot.Node(self.__label, label=content, margin="0.3",
                                             style="filled", shape="rect", color=self.__color)
        else:
            content = f"{self.__label} \l\t{self.__content}\l"
            if self.is_singleton:
                self.__dot_Node = pydot.Node(self.__label, label=content, margin="0.3", style="filled", shape="rect",
                                             color="limegreen")
            else:
                self.__dot_Node = pydot.Node(self.__label, label=content, margin="0.3", style="filled", shape="rect")

    def get_dot_node(self):
        return self.__dot_Node

    def __eq__(self, other):
        return self.__label == other.get_label()

    def __hash__(self):
        return hash((self.__label, self.__start_address))

    def __iter__(self):
        self.__index = 0
        return self

    def __next__(self) -> Instruction:
        if self.__index >= len(self.__instr_list):
            raise StopIteration
        value = self.__instr_list[self.__index]
        self.__index += 1
        return value

    def __getitem__(self, item):
        return self.__instr_list[item]

    def __len__(self):
        return len(self.__instr_list)


class Edge:
    def __init__(self, src, dest):
        self.__src = src
        self.__dest = dest

    def get_source(self):
        return self.__src

    def get_destination(self):
        return self.__dest


class FlowGraph:
    def __init__(self, asm_code):
        self.__asm_code = asm_code
        self.nodes = []
        self.edges = {}

        self.__set_nodes()
        self.__set_edges()

        self.usage_info = {}
        self.__color_type = "ylorrd9"
        self.__color_id = 9

    def add_node(self, node):
        if node in self.nodes:
            print("This node is already in graph!")
        else:
            self.nodes.append(node)
            self.edges[node] = []

    def add_edge(self, edge):
        src = edge.get_source()
        dest = edge.get_destination()
        if not (src in self.nodes and dest in self.nodes):
            print("Can not create edge, no such nodes!")
        self.edges[src].append(dest)

    def __set_nodes(self):
        instruction_list = []
        start_addr = -1
        label = ""
        for addr, instr in self.__asm_code.items():
            if instr.get_label():
                if instruction_list:
                    self.add_node(Node(label, start_addr, instruction_list))
                    instruction_list.clear()
                start_addr = addr
                label = instr.get_label()
            instruction_list.append(instr)

        if instruction_list:
            self.add_node(Node(label, start_addr, instruction_list))

    def __set_edges(self):
        i = 0
        while i < len(self.nodes):
            jmp_target = self.nodes[i].get_jump_target()

            if self.nodes[i].ends_with_ret_inst():
                i += 1
                continue

            if jmp_target:
                if self.nodes[i].ends_with_br_inst() and i + 1 < len(self.nodes):
                    self.add_edge(Edge(self.nodes[i], self.nodes[i + 1]))
                jmp_node = self.find_node_with_label(jmp_target)
                if jmp_node:
                    self.add_edge(Edge(self.nodes[i], jmp_node))
            elif i + 1 < len(self.nodes):
                self.add_edge(Edge(self.nodes[i], self.nodes[i + 1]))
            i += 1

    def get_bb_addresses(self):
        return [node.get_address() for node in self.nodes]

    def set_nodes_usage_info(self):
        for node in self.nodes:
            info = self.usage_info.get(node.get_address())
            if info:
                node.set_usage_info(info)
            else:
                # print(f"Cannot find usage info for bb with address: {node.get_address()} in collect file")
                node.set_usage_info("empty")

    def find_node_with_label(self, label):
        for node in self.nodes:
            if node.get_label() == label:
                return node
        return None

    def __max_percent(self):
        max_p = 0
        for node in self.nodes:
            tmp_p = node.get_execution_count()
            if tmp_p != "empty":
                if max_p < int(tmp_p):
                    max_p = int(tmp_p)
        return max_p

    def __set_color(self):
        max_p = self.__max_percent()
        num = round(max_p / self.__color_id + 0.5)
        color_list = [num * (i + 1) for i in range(self.__color_id)]

        for node in self.nodes:
            tmp_p = node.get_execution_count()
            if tmp_p != "empty":
                for i, color in enumerate(color_list):
                    if int(tmp_p) <= color:
                        node.set_color(f"/{self.__color_type}/{i + 1}")
                        break

    def __set_dot_nodes(self, graph: pydot.Dot):
        for node in self.nodes:
            graph.add_node(node.get_dot_node())

    def __set_dot_edges(self, graph: pydot.Dot):
        for src in self.nodes:
            for dest in self.edges[src]:
                graph.add_edge(pydot.Edge(src=src.get_label(), dst=dest.get_label()))

    def find_singleton_bbs(self):
        for src in self.nodes:
            for dest in self.edges[src]:
                if dest.has_singleton_inst() and self.edges.get(dest):
                    for dd in self.edges[dest]:
                        if dd in self.edges[src]:
                            dest.is_singleton = True

    def draw_graph(self, out_dot_file):

        # In some cases DOT lib hang over,
        # Processing each function should not be longer than 10 minutes
        signal.signal(signal.SIGALRM, self.__handler)
        signal.alarm(600)

        if self.usage_info:
            self.__set_color()

        for node in self.nodes:
            node.create_dot_node()

        graph = pydot.Dot("_graph", graph_type="digraph")

        self.__set_dot_nodes(graph)
        self.__set_dot_edges(graph)
        graph.write_dot(out_dot_file)

        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

    def __handler(self, signum, frame):
        raise TimeoutError("Function time out!!!")

    def __str__(self):
        result = ''
        for src in self.nodes:
            for dest in self.edges[src]:
                result = result + src.get_label() + \
                         '-->' + dest.get_label() + '\n'
        return result[:-1]