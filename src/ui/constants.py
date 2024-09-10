# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import os
from pathlib import Path

ASM_GRAPH: str = "asm_graph.py"
RUN_SPEC: str = "run_spec.py"
STYLE_CSS: str = "styles/main.css"
README: str = "README.md"
BBES_GATHERER = "bbes_gatherer.py"
EVALUATE_VERSIONS = "evaluate_versions.py"
PLUGINS_JSON = "plugins.json"
BASIC_PLUGINS = "basic.py"

WINDOW_BASE_TITLE: str = "ASMGraph"
BASE_WORK_DIR_NAME: str = "untitled"
RECENT_PROJECTS_FILE_NAME: str = "recent_projects.json"
DEFAULT_WORK_DIR: str = "/var/tmp/ASMGraphWD"

GTK_STYLE_PROVIDER_PRIORITY_APPLICATION: int = 600
DEFAULT_TRANSITION_DURATION: int = 500
PANE_SEPERATOR_POS: int = 300

DUMMY_BASE_URL: str = "file://"
SEARCH_PLACEHOLDER_TEXT: str = "Search..."

UI_DIR: str = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR: str = os.path.dirname(os.path.dirname(UI_DIR))

RECENT_PROJECTS_FILE: str = os.path.join(DEFAULT_WORK_DIR, RECENT_PROJECTS_FILE_NAME)

MAIN_WINDOW_WIDTH: int = 800
MAIN_WINDOW_HEIGHT: int = 630

ERROR_WINDOW_WIDTH: int = 600
ERROR_WINDOW_HEIGHT: int = 150

HELP_WINDOW_WIDTH: int = 1000
HELP_WINDOW_HEIGHT: int = 500

DOT_WINDOW_WIDTH: int = 1200
DOT_WINDOW_HEIGHT: int = 800

CUSTOM_PLUGIN_FUNCTION_NAME: str = "run"

DOWNLOADS_DIR = str(Path.home() / "Downloads")
