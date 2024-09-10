# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

from enum import Enum


class JSONKeywords(str, Enum):
    PROJECT_NAME = "project_name"
    FOLDER_PATH = "folder_path"
    PROJECT_TYPE = "project_type"

class CSSClasses(str, Enum):
    BUTTON_STYLE_1 = "button-style-1"
    BUTTON_STYLE_2 = "button-style-2"
    LABEL_ERROR = "label-error"
    LABEL_DEFAULT = "label-default"
    MAIN_BOX = "main-box"
    CONTENT_BOX = "content-box"
    CHECKBOX = "checkbox"
    RADIOBUTTON_BOX = "radio-button-box"
    INNER_BOX_BIN = "inner-box-bin"
    ACTION_BOX = "action-box"
    FOOTER = "footer"
    NEW_PROJECT_BTN = "new-project-btn"
    VIS_BOX = "vis-box"
    SPEC_BOX = "spec-box"
    XDOT_WIDGET = "xdot-widget"
    GRAPH_VIS_LEFT_PANEL = "graph_vis_left_panel"
    DOT_FILE_BOX = "dot_files_box"
    VIS_BOX_SEARCH = "viz_box_search"
    NAME_BUTTON = "name_btn"
    EXEC_BTN = "exec_btn"
    DOTS = "dots"
    FILE_BOX = "file_box"
    ALIGN_LEFT = "align_left"
    FUNCTION_NAME = "function_name"
    SELECTED_BUTTON = "selected_btn"
    PROJECT_NAME = "project_name"
    MENU_ITEM = "menu_item"
    VISUALIZER_DIVIDER = "visualizer-divider"
    RUN_PLUGINS_MENU_ITEM = "run_plugins_menu_item"
    DOT_FILES = "dot_files"
    NEW_PLUGIN_DIALOG = "new_plugin_dialog"
    RUN_PLUGINS = "run_plugins"
    PLUGINS_SUBMODULE = "plugins_submenu"
    SUMMARY_INFO = "summary_info"
    COMPARE_BTN = "compare-btn"

class ViewsLabels(str, Enum):
    # New project
    VISUALIZE = "Visualize"
    SPEC = "SPEC"

    CREATE = "Create"
    CANCEL = "Cancel"

    PROJECT_NAME = "Project name"
    LOCATION = "Project work dir"

    # Visualize
    BIN_RADIO = "Bin"
    ASM_RADIO = "Asm"
    DISAS_PATH = "Disas path"
    BIN_PATH = "Bin path"
    ASM_PATH = "Asm path"
    FUSION = "Check instruction fusion"
    SINGLETON = "Mark BB with single instructions"
    BBEXEC_PATH = "BBExec file path"

    # SPEC
    BASE = "Base"
    PICK = "Pick"
    TUNE = "Tune"

    SPEC_CONFIG = "Path to config.cfg file"
    INTRATE = "Run intrate tests"
    FPRATE = "Run fprate tests"
    REBUILD = "Rebuild tests"
    CLEAN = "Clean previous build"
    REPORTABLE = "Reportable"
    DEFINES = "Defines"
    SPEC_PATH = "Path to SPEC directory"


class Events(str, Enum):
    CREATE = 'create'
    CANCEL = 'cancel'
    CLICKED = 'clicked'
    CHANGED = 'changed'
    ACTIVATE = 'activate'
    TOGGLED = 'toggled'
    DESTROY = 'destroy'
    DELETE = 'delete-event'
    RELOAD = 'reload'
    VISUALIZE_DOT = 'visualize-dot'
    COMPARE = 'compare'
    DEACTIVATE_COMPARISON = 'deactivate-comparison'
    SELECT_FUNC = 'select-func'
    BUTTON_PRESS = 'button-press-event'
    TOTAL_DYN_INST = 'total_dyn_inst'


class ProjectType(str, Enum):
    BASIC = "basic"
    SPEC = "spec"
    SPEC_TUNE = "spec_tune"


class DotFileVisualizerOrientations(str, Enum):
    LEFT = "left"
    RIGHT = "right"
