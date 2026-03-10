# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import about_panel
from .settings_panel import (
    color_attributes_settings_panel,
    display_settings_panel,
    global_color_settings_panel,
    settings_panel,
)
from .tools_panel import (
    color_by_position_tool_panel,
    random_color_tool_panel,
    simple_fill_tool_panel,
    tools_panel,
)

classes = [
    about_panel.MC_PT_about_panel,
    settings_panel.MC_PT_settings_panel,
    display_settings_panel.MC_PT_display_settings_panel,
    color_attributes_settings_panel.MC_PT_color_attributes_settings_panel,
    tools_panel.MC_PT_tools_panel,
    random_color_tool_panel.MC_PT_random_color_tool_panel,
    global_color_settings_panel.MC_PT_global_color_settings_panel,
    color_by_position_tool_panel.MC_PT_color_by_position_tool_panel,
    simple_fill_tool_panel.MC_PT_simple_fill_tool_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    simple_fill_tool_panel.cleanup_preset_previews()
