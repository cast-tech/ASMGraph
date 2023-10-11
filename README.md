# ASMGraph

---

## Overview

ASMGraph is a simple framework which tends to help compiler developers who work in RISC-V architecture. \
This framework intends to:

* Visualize functions assembly code through xdot
* Highlight executed and the hottest BBs in each function
* Extract singleton BBs from the whole function
* Find several instruction fusion cases like:
  * Extending (SI->DI, HI->DI)
  * Integer indexed loads
  * Load with preincrement
  * Loads from constant addresses
  * Address and constant formation
  * Double address and constant formation
* Computes executed instructions count like `llvm-mca`


---

## Installing

Install the libraries from **requirements.txt**

```
pip install -r requirements.txt
```

or

```
pip3 install -r requirements.txt
```

---

## Usage

### asm_graph.py options:

* `-h, --help`        Show this help message and exit
* `-a ASM, --asm ASM` Path to assembler file.
* `-b BIN, --bin BIN` Path to the binary file.
* `-d OBJDUMP, --objdump OBJDUMP` Path to the disassembler (riscv-objdump).
* `-f FUNC, --func FUNC` The name of the function that should be extracted. \
                         By default will produce all functions from the text segment.
* `-c COLLECT, --collect COLLECT` Path to the collect file.
* `-i, --fusion`         Check instruction fusion.
* `--dot`                Create dot graph for functions.
* `--min_exec_count MIN_EXEC_COUNT` \
                        BB should have at least mentioned amount execution count to be processed in fusion checkers.
* `-s, --singletons`    Collect singleton basic blocks into the singletons.xlsx.
* `-o OUTPUT, --output OUTPUT` The name of the out directory. (by default: `cwd`/output)


### Usage examples:

ASMGraph can be used in two modes, with and without **collect** file.\
Providing collect file opens several opportunities like highlighting the hottest BB \
or computing instructions group like `llvm-mca`.

To run ASMGraph either get asm of your project or put that in us just by passing the disassembler path.

**NOTE: If you disassemble yourself you must pass `--no-show-raw-insn` option to disassembler**

---

1. Here is an example to run ASMGraph through binary.

```commandline
./asm_graph.py -b ./path/to/test.exe --objdump /full/path/to/riscv-**objdump -o output
```
In this case, the output directory will contain all function bodies extracted in a separate file. \
This option is permanent and done in any case.

---
2. To run ASMGraph through your disassembled file run the following command.

```commandline
./asm_graph.py -a ./path/to/test.asm -o output
```

---

3. In order to visualize `my_function` run the following command.

```commandline
./asm_graph.py -a ./path/to/test.asm -f my_function --dot -o output
```
After this, the output directory will contain my_function.asm and my_function.dot files. \
For function body and visualization files, respectively.

Unfortunately, this option may slow down execution performance. \
We set a time limit for each function in 10 minutes.

---

4. To apply execution info in visualization also add `-c` option.

```commandline
./asm_graph.py -a ./path/to/test.asm -c ./path/to/test.collect -f my_function --dot -o output
```
BBs that did not execute at all will be colored in blue and most executed in dark red.

---

5. Io run fusion checkers you need to run the following command

```commandline
./asm_graph.py -a ./path/to/test.asm --fusion -o output
```

After the execution in the output directory, you can find the test.xlsx file.\
Which contains the results of each checker separated into responding sheets.

**SUGGESTION:**\
Run checkers with collect info to get only more actual and interesting cases.

```commandline
./asm_graph.py -a ./path/to/test.asm -c ./path/to/test.collect --fusion -o output
```

ASMGraph gets read each BB which has less than `1M` dynamic instruction. \
To adjust that value use the `--min_exec_count` option. \
For example, to check only BBs which have at least 5M execution use this command line.

```commandline
./asm_graph.py -a ./path/to/test.asm -c ./path/to/test.collect --fusion --min_exec_count 5000000 -o output
```

---

6. In order to extract singleton BBs run the following command.

```commandline
./asm_graph.py -a ./path/to/test.asm -s -o output
```


# How to compare two compiler versions

We are providing a small script that will help with that issue.\
`evaluate_versions.py` script intends to compare the performance of two compilers.

For example, you have *collect files gathered in `dir_1` and `dir_2` directories, \
respectively for C1 and C2 compilers. To compare them just run the following command line.

```commandline
./evaluate_versions.py --first-collects-dir ./dir_1 --second-collects-dir ./dir_2
```

In the current working directory will be created `evaluation_result.xlsx` sheet.\
That contains the comparison of each *collect file separated sheet by sheet.\
Name of *collect files such important, the script tries to compare only collects which have the same name.\n

Besides, comparing by collect file, the script provides also general comparison (sheet name `general_diff`).\
That is the difference of while evaluation.
