# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import glob
import os
import subprocess
from typing import Dict, Union, List

from src.ui.constants import ROOT_DIR, ASM_GRAPH, BBES_GATHERER, EVALUATE_VERSIONS
from src.ui.error_handler import ErrorWindow
from src.ui.keywords import ViewsLabels

class CommandBuilder:
    @staticmethod
    def make_visualize_command(values: Dict[str, Union[str, bool]]) -> str:
        if not values:
            return ""

        command: str = os.path.join(ROOT_DIR, ASM_GRAPH)
        command += " --dot"
        if ViewsLabels.ASM_PATH in values:
            command += f" -a {values[ViewsLabels.ASM_PATH]}"
        else:
            command += f" -b {values[ViewsLabels.BIN_PATH]}" \
                       f" --objdump {values[ViewsLabels.DISAS_PATH]}"

        if ViewsLabels.BBEXEC_PATH in values:
            command += f" -c {values[ViewsLabels.BBEXEC_PATH]}"

        if values.get(ViewsLabels.SINGLETON):
            command += f" --singletons"

        command += f" -o {values[ViewsLabels.LOCATION]}"
        return command

    @staticmethod
    def make_spec_collect_bbe_command(values: Dict[str, Union[str, bool]]) -> str:
        if not values:
            return ""
        command: str = os.path.join(ROOT_DIR, BBES_GATHERER)
        command += f" --spec_dir {values[ViewsLabels.SPEC_PATH]}"

        if values.get(ViewsLabels.BASE):
            command += f" --base"
        if values.get(ViewsLabels.PICK):
            command += f" --pick"

        command += f" -o {values[ViewsLabels.LOCATION]}"
        return command

    def make_spec_visualize_commands(self, proj_dir: str, disas_path: str) -> Dict[str, str]:
        if not proj_dir or not disas_path:
            return {}

        commands = {}

        benches = glob.glob(os.path.join(proj_dir, '*'))

        for bench in benches:
            for file_path in glob.glob(os.path.join(bench, '*')):
                if os.access(file_path, os.X_OK):
                    file_name = os.path.basename(file_path)

                    vis_vals = {
                        ViewsLabels.BIN_PATH: file_path,
                        ViewsLabels.DISAS_PATH: disas_path,
                        ViewsLabels.BBEXEC_PATH: bench,
                        ViewsLabels.LOCATION: os.path.join(proj_dir, file_name + "_dots")
                    }
                    commands[file_path] = self.make_visualize_command(vis_vals)

        return commands

    @staticmethod
    def make_evaluation_command(first_bbe_dir: str, second_bbe_dir: str, output_path: str) -> str:
        command: str = os.path.join(ROOT_DIR, EVALUATE_VERSIONS)
        if not os.path.isdir(first_bbe_dir) or not os.path.isdir(second_bbe_dir):
            return ""
        command += f" --fd {first_bbe_dir} --sd {second_bbe_dir} --all"
        command += f" -o {output_path}"
        return command


    @staticmethod
    def execute(command: str) -> int:
        if not command:
            return -1

        args: List[str] = command.split()

        try:
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except Exception as e:
            ErrorWindow(f"Subprocess ERROR: {e}")
            raise e

        ret_code = proc.wait()
        return ret_code
