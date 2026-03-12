# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import (
    add_color_by_position,
    add_random_color,
    attribute_transfer,
    color_adjustments,
    color_by_selection,
    display_vertex_colors,
    open_documentation,
    reset_vertex_colors,
    simple_fill,
    smooth_vertex_colors,
    symmetrize_vertex_colors,
)

classes = [
    display_vertex_colors.MC_OT_display_vertex_colors,
    display_vertex_colors.MC_OT_enable_rgb_display,

    add_random_color.MC_OT_add_random_color,
    add_random_color.MC_OT_add_random_color_by_object,
    open_documentation.MC_OT_open_documentation,
    reset_vertex_colors.MC_OT_reset_color,

    add_color_by_position.MC_OT_add_color_by_position,
    add_color_by_position.MC_OT_reset_color_by_position_gradient,

    simple_fill.MC_OT_simple_fill,
    simple_fill.MC_OT_add_preset_color,
    simple_fill.MC_OT_remove_preset_color,
    simple_fill.MC_OT_new_palette,
    simple_fill.MC_OT_use_preset_color,

    smooth_vertex_colors.MC_OT_smooth_vertex_colors,

    color_by_selection.MC_OT_color_by_selection,

    color_adjustments.MC_OT_color_adjustments,

    attribute_transfer.MC_OT_attribute_transfer,

    symmetrize_vertex_colors.MC_OT_symmetrize_vertex_colors,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
