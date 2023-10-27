#!/usr/bin/python

# Now that we have specific instruction counts, group them.
#
# We put each instruction into a group as we often need to think about
# them as groups (say conditional branches, ALU, LOGICAL, etc).
#
# What would be even better would be metadata indicating functional
# units, latency, etc.  Future work.
#
# I'm adding instructions in here on-demand.  But we really should just
# pour over the ISA spec front-to-back and cover them all.  I just
# haven't had the time and want to focus a bit on extracting useful
# data right now.
#
# Note that vendor extensions show up as illegal instructions from
# the qemu plugin.  cboz shows up as "lq" of all things...  Weird.
#

MAX_FUNCTION_NAME_LENGTH = 100

binary_branch_instructions = ["beqz", "bnez", "blez", "bgez", "bltz", "bgtz"]
ternary_branch_instructions = ["beq", "bne", "bge", "blt", "bgt", "ble", "bgtu", "bleu", "bltu", "bgeu"]
branch_instructions = binary_branch_instructions + ternary_branch_instructions

# jump_instructions = ["j", "jr", "ret", ]
jump_instructions = ["j", "jal", "jr", "jalr", "ret", "call", "tail", "frrm"]

terminate = ["ret", "ra", "ebreak", "frflags", "fsflags", "ecall", "nop", "cbo.zero"]

loads = ["lb", "lbu", "lh", "lhu", "lw", "lwu", "ld", "lq"]
stores = ["sb", "sh", "sw", "sd", "st"]
conditional = ["seqz", "snez", "sltz", "sgtz", "slti", "sltiu", "sgt", "sgtu"]
extend = ["zext.b", "zext.h", "zext.w", "sext.w", "sext.b", "sext.h"]
binary_instructions = binary_branch_instructions + loads + stores + conditional + extend + \
                      ["lui", "li", "mv", "move", "la", "lla", "neg", "negw", "auipc"]

INSN_GROUP_DICT = {
    'prefetch.i': 'hints',
    'prefetch.r': 'hints',
    'prefetch.w': 'hints',
    'pause': 'hints',

    'unimp': 'misc',
    'ebreak': 'misc',
    'sbreak': 'misc',

    'ret': 'jumps',
    'jr': 'ind_jumps',
    'jalr': 'ind_jumps',
    'j': 'jumps',
    'jal': 'jumps',
    'call': 'jumps',
    'tail': 'jumps',
    'jump': 'jumps',

    'nop': 'nops',

    'lui': 'alu',
    'li': 'alu',
    'mv': 'alu',
    'move': 'alu',

    'zext.b': 'extensions',

    'and': 'logical',
    'andi': 'logical',

    'beqz': 'cbr',
    'beq': 'cbr',
    'blez': 'cbr',
    'bgez': 'cbr',
    'bge': 'cbr',
    'bgeu': 'cbr',
    'ble': 'cbr',
    'bleu': 'cbr',
    'bltz': 'cbr',
    'bgtz': 'cbr',
    'blt': 'cbr',
    'bltu': 'cbr',
    'bgt': 'cbr',
    'bgtu': 'cbr',
    'bnez': 'cbr',
    'bne': 'cbr',

    'add': 'alu',
    'addi': 'alu',

    'la': 'alu',
    'lla': 'alu',
    'la.tls.gd': 'alu',
    'la.tls.ie': 'alu',

    'neg': 'alu',

    'sll': 'shifts',
    'slli': 'shifts',
    'srl': 'shifts',
    'srli': 'shifts',
    'sra': 'shifts',
    'srai': 'shifts',

    'sub': 'alu',

    'lb': 'loads',
    'lbu': 'loads',
    'lh': 'loads',
    'lhu': 'loads',
    'lw': 'loads',

    'not': 'logical',
    'or': 'logical',
    'ori': 'logical',

    'auipc': 'alu',

    'seqz': 'conditional',
    'snez': 'conditional',
    'sltz': 'conditional',
    'sgtz': 'conditional',
    'slti': 'conditional',
    'slt': 'conditional',
    'sltiu': 'conditional',
    'sltu': 'conditional',
    'sgt': 'conditional',
    'sgtu': 'conditional',

    'sb': 'stores',
    'sh': 'stores',
    'sw': 'stores',

    'fence': 'atomics',
    'fence.i': 'atomics',
    'fence.tso': 'atomics',

    'rdcycle': 'misc',
    'rdinstret': 'misc',
    'rdtime': 'misc',
    'rdcycleh': 'misc',
    'rdinstreth': 'misc',
    'rdtimeh': 'misc',
    'ecall': 'misc',
    'scall': 'misc',

    'xor': 'logical',
    'xori': 'logical',

    'lwu': 'loads',
    'ld': 'loads',
    'sd': 'stores',

    'sext.w': 'extensions',
    'addw': 'alu',
    'addiw': 'alu',
    'negw': 'alu',

    'sllw': 'shifts',
    'slliw': 'shifts',
    'srlw': 'shifts',
    'srliw': 'shifts',
    'sraiw': 'shifts',
    'slli.uw': 'shifts',
    'sraw': 'shifts',

    'subw': 'alu',

    'lr.w': 'atomics',
    'sc.w': 'atomics',
    'amoadd.w': 'atomics',
    'amoswap.w': 'atomics',
    'amoand.w': 'atomics',
    'amoor.w': 'atomics',
    'amoxor.w': 'atomics',
    'amomax.w': 'atomics',
    'amomaxu.w': 'atomics',
    'amomin.w': 'atomics',
    'amominu.w': 'atomics',
    'lr.w.aq': 'atomics',
    'sc.w.aq': 'atomics',
    'amoadd.w.aq': 'atomics',
    'amoswap.w.aq': 'atomics',
    'amoand.w.aq': 'atomics',
    'amoor.w.aq': 'atomics',
    'amoxor.w.aq': 'atomics',
    'amomax.w.aq': 'atomics',
    'amomaxu.w.aq': 'atomics',
    'amomin.w.aq': 'atomics',
    'amominu.w.aq': 'atomics',
    'lr.w.rl': 'atomics',
    'sc.w.rl': 'atomics',
    'amoadd.w.rl': 'atomics',
    'amoswap.w.rl': 'atomics',
    'amoand.w.rl': 'atomics',
    'amoor.w.rl': 'atomics',
    'amoxor.w.rl': 'atomics',
    'amomax.w.rl': 'atomics',
    'amomaxu.w.rl': 'atomics',
    'amomin.w.rl': 'atomics',
    'amominu.w.rl': 'atomics',
    'lr.w.aq.rl': 'atomics',
    'sc.w.aq.rl': 'atomics',
    'amoadd.w.aq.rl': 'atomics',
    'amoswap.w.aq.rl': 'atomics',
    'amoand.w.aq.rl': 'atomics',
    'amoor.w.aq.rl': 'atomics',
    'amoxor.w.aq.rl': 'atomics',
    'amomax.w.aq.rl': 'atomics',
    'amomaxu.w.aq.rl': 'atomics',
    'amomin.w.aq.rl': 'atomics',
    'amominu.w.aq.rl': 'atomics',
    'lr.d': 'atomics',
    'sc.d': 'atomics',
    'amoadd.d': 'atomics',
    'amoswap.d': 'atomics',
    'amoand.d': 'atomics',
    'amoor.d': 'atomics',
    'amoxor.d': 'atomics',
    'amomax.d': 'atomics',
    'amomaxu.d': 'atomics',
    'amomin.d': 'atomics',
    'amominu.d': 'atomics',
    'lr.d.aq': 'atomics',
    'sc.d.aq': 'atomics',
    'amoadd.d.aq': 'atomics',
    'amoswap.d.aq': 'atomics',
    'amoand.d.aq': 'atomics',
    'amoor.d.aq': 'atomics',
    'amoxor.d.aq': 'atomics',
    'amomax.d.aq': 'atomics',
    'amomaxu.d.aq': 'atomics',
    'amomin.d.aq': 'atomics',
    'amominu.d.aq': 'atomics',
    'lr.d.rl': 'atomics',
    'sc.d.rl': 'atomics',
    'amoadd.d.rl': 'atomics',
    'amoswap.d.rl': 'atomics',
    'amoand.d.rl': 'atomics',
    'amoor.d.rl': 'atomics',
    'amoxor.d.rl': 'atomics',
    'amomax.d.rl': 'atomics',
    'amomaxu.d.rl': 'atomics',
    'amomin.d.rl': 'atomics',
    'amominu.d.rl': 'atomics',
    'lr.d.aq.rl': 'atomics',
    'sc.d.aq.rl': 'atomics',
    'amoadd.d.aq.rl': 'atomics',
    'amoswap.d.aq.rl': 'atomics',
    'amoand.d.aq.rl': 'atomics',
    'amoor.d.aq.rl': 'atomics',
    'amoxor.d.aq.rl': 'atomics',
    'amomax.d.aq.rl': 'atomics',
    'amomaxu.d.aq.rl': 'atomics',
    'amomin.d.aq.rl': 'atomics',
    'amominu.d.aq.rl': 'atomics',

    'mul': 'multiply',
    'mulh': 'multiply',
    'mulhu': 'multiply',
    'mulhsu': 'multiply',
    'div': 'div_rem',
    'divu': 'div_rem',
    'rem': 'div_rem',
    'remu': 'div_rem',
    'mulw': 'multiply',
    'divw': 'div_rem',
    'divuw': 'div_rem',
    'remw': 'div_rem',
    'remuw': 'div_rem',

    'flh': 'FP load',
    'fsh': 'FP store',
    'fmv.x.h': 'FP move/convert',
    'fmv.h.x': 'FP move/convert',
    'fmv.h': 'FP move/convert',
    'fmv.w.x': 'FP move/convert',
    'fmv.x.w': 'FP move/convert',
    'fneg.h': 'FP ALU',
    'fabs.h': 'FP ALU',
    'fsgnj.h': 'FP ALU',
    'fsgnjn.h': 'FP ALU',
    'fsgnjx.h': 'FP ALU',
    'fadd.h': 'FP ALU',
    'fsub.h': 'FP ALU',
    'fmul.h': 'FP ALU',
    'fdiv.h': 'FP ALU',
    'fsqrt.h': 'FP ALU',
    'fmin.h': 'FP ALU',
    'fmax.h': 'FP ALU',
    'fmadd.h': 'FP ALU',
    'fnmadd.h': 'FP ALU',
    'fmsub.h': 'FP ALU',
    'fnmsub.h': 'FP ALU',
    'fcvt.w.h': 'FP ALU',
    'fcvt.s.w': 'FP ALU',
    'fcvt.s.l': 'FP ALU',
    'fcvt.wu.h': 'FP ALU',
    'st': 'stores',
    'sext.b': 'extensions',
    'sext.h': 'extensions',
    'zext.h': 'extensions',
    'zext.w': 'extensions',
    'add.uw': 'alu',
    'andn': 'logical',
    'xnor': 'logical',
    'orn': 'logical',
    'rori': 'shifts',
    'bset': 'bitmanip',
    'bext': 'bitmanip',
    'bexti': 'bitmanip',
    'bseti': 'bitmanip',
    'binvi': 'bitmanip',
    'binv': 'bitmanip',
    'bclri': 'bitmanip',
    'bclr': 'bitmanip',
    'max': 'minmax',
    'min': 'minmax',
    'minu': 'minmax',
    'maxu': 'minmax',
    'flt.s': 'FP conditional',
    'flt.d': 'FP conditional',
    'fle.d': 'FP conditional',
    'feq.s': 'FP conditional',
    'feq.d': 'FP conditional',
    'flt': 'FP conditional',
    'fsd': 'FP store',
    'fld': 'FP load',
    'fsw': 'FP store',
    'flw': 'FP load',
    'fmul': 'FP multiply',
    'fmul.s': 'FP multiply',
    'fmul.d': 'FP multiply',
    'fadd': 'FP ALU',
    'fadd.s': 'FP ALU',
    'fadd.d': 'FP ALU',
    'fsub.s': 'FP ALU',
    'fsub.d': 'FP ALU',
    'fneg.s': 'FP ALU',
    'fneg.d': 'FP ALU',
    'fabs.d': 'FP ALU',
    'fabs.s': 'FP ALU',
    'fmin.s': 'FP ALU',
    'fmax.s': 'FP ALU',
    'fmax.d': 'FP ALU',
    'fmadd.d': 'FP ALU',
    'fmsub.d': 'FP ALU',
    'fdiv.s': 'FP DIV/SQRT',
    'fdiv.d': 'FP DIV/SQRT',
    'sh1add': 'shadd',
    'sh2add': 'shadd',
    'sh3add': 'shadd',
    'sh1add.uw': 'shadd',
    'sh2add.uw': 'shadd',
    'sh3add.uw': 'shadd',
    'fmv.s.x': 'FP move/convert',
    'illegal': 'illegal/special',
    'fmv.s.w': 'FP move/convert',
    'fcvt.d.l': 'FP move/convert',
    'fcvt.d.s': 'FP move/convert',
    'fmv.x.d': 'FP move/convert',
    'fcvt.w.d': 'FP move/convert',
    'fmv.s': 'FP move/convert',
    'fle.s': 'FP comparison between floating-point registers',
    'fcvt.w.s': 'FP move/convert',
    'fcvt.d.lu': 'FP move/convert',
    'fcvt.d.w': 'FP move/convert',
    'fcvt.lu.d': 'FP move/convert',
    'fcvt.l.d': 'FP move/convert',
    'fcvt.d.wu': 'FP move/convert',
    'fcvt.wu.d': 'FP move/convert',
    'fcvt.s.lu': 'FP move/convert',
    'fcvt.lu.s': 'FP move/convert',
    'fcvt.s.d': 'FP move/convert',
    'fcvt.wu.s': 'FP move/convert',
    'fmv.d': 'FP move/convert',
    'fmv.d.x': 'FP move/convert',
    'fmv.x.s': 'FP move/convert',
    'fcvt.s.wu': 'FP move/convert',
    'frrm': 'FP special',
    'frflags': 'FP special',
    'fsflags': 'FP special',
    'fsgnj.d': 'FP ALU',
    'fsgnj.s': 'FP ALU',
    'ctz': 'bitmanip',
    'ctzw': 'bitmanip',
    'clz': 'bitmanip',
    'clzw': 'bitmanip',
    'cpop': 'bitmanip',
    'orc.b': 'bitmanip',
    'rev8': 'bitmanip',
    'roriw': 'shifts',
    'fsqrt.d': 'FP ALU',
    'fsqrt.s': 'FP ALU',
    'lq': 'loads',

    'ror': 'shifts',
    'rorw': 'shifts',
    'rol': 'shifts',
    'rolw': 'shifts',
    'label': 'address',
    'cbo.zero': 'CMO'
}
