# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import (
    color_by_position_tool_properties,
    display_settings_properties,
    global_color_settings_properties,
    random_color_tool_properties,
    simple_fill_tool_properties,
)

classes = [
    random_color_tool_properties.RandomColorToolProperties,
    global_color_settings_properties.GlobalColorSettingsProperties,
    color_by_position_tool_properties.ColorByPositionToolProperties,
    simple_fill_tool_properties.SimpleFillToolProperties,
    display_settings_properties.DisplaySettingsProperties,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.more_colors_random_color_tool = bpy.props.PointerProperty(
        type=random_color_tool_properties.RandomColorToolProperties)
    bpy.types.Scene.more_colors_global_color_settings = bpy.props.PointerProperty(
        type=global_color_settings_properties.GlobalColorSettingsProperties)
    bpy.types.Scene.more_colors_color_by_position_tool = bpy.props.PointerProperty(
        type=color_by_position_tool_properties.ColorByPositionToolProperties)
    bpy.types.Scene.more_colors_simple_fill_tool = bpy.props.PointerProperty(
        type=simple_fill_tool_properties.SimpleFillToolProperties)
    bpy.types.Scene.more_colors_display_settings = bpy.props.PointerProperty(
        type=display_settings_properties.DisplaySettingsProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.more_colors_random_color_tool
    del bpy.types.Scene.more_colors_global_color_settings
    del bpy.types.Scene.more_colors_color_by_position_tool
    del bpy.types.Scene.more_colors_simple_fill_tool
    del bpy.types.Scene.more_colors_display_settings
