# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import json
import os

from src.ui.constants import ROOT_DIR

FUNCS_BLACK_LIST_FILE_PATH = os.path.join(ROOT_DIR, "functions_blacklist.json")

def load_blacklist():
    if not os.path.exists(FUNCS_BLACK_LIST_FILE_PATH):
        print(f"Warning: Cannot find such file: {FUNCS_BLACK_LIST_FILE_PATH}")
        return {}
    with open(FUNCS_BLACK_LIST_FILE_PATH, 'r') as f:
        return json.load(f)

def save_blacklist(black_list):
    with open(FUNCS_BLACK_LIST_FILE_PATH, 'w') as json_file:
        json.dump(black_list, json_file)

def append_function_to_blacklist(function_name: str):
    try:
        black_list = load_blacklist()
        if function_name in black_list:
            return
        black_list.append(function_name)
        save_blacklist(black_list)
    except Exception as e:
        print(f"Cannot add function to blacklist: {e}")
