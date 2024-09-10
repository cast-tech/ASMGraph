# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

# Example of custom plugin for the `graph` module.
# This plugin calculates the length of the basic block.


from src.graph import Node
from typing import List


# Plugin must have a `run` function, which receives a `Node` object as input.
# The function must return a list of dictionaries, with the processing results.
def run(basic_block: Node) -> List[dict]:
    """
    This function calculates the length of the basic block.

    :param basic_block: The Node object to be processed by the plugin.
    :type basic_block: Node
    :return: A list of dictionaries containing processed information.
    :return: List[dict]
    """

    return [{f"{basic_block.get_label()}": f"len - {len(basic_block)}"}]
