# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import (
    add_color_by_position,
    add_random_color,
    display_vertex_colors,
    open_documentation,
    reset_vertex_colors,
    simple_fill,
)

classes = [
    display_vertex_colors.MC_OT_display_vertex_colors,

    add_random_color.MC_OT_add_random_color,
    open_documentation.MC_OT_open_documentation,
    reset_vertex_colors.MC_OT_reset_color,

    add_color_by_position.MC_OT_add_color_by_position,
    add_color_by_position.MC_OT_initialize_color_by_position_tool,
    add_color_by_position.MC_OT_reset_color_by_position_gradient,

    simple_fill.MC_OT_simple_fill,
    simple_fill.MC_OT_add_preset_color,
    simple_fill.MC_OT_remove_preset_color,
    simple_fill.MC_OT_use_preset_color,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
