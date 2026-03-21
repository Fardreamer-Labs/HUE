# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import (
    attribute_transfer_tool_properties,
    color_adjustments_tool_properties,
    color_by_position_tool_properties,
    color_by_selection_tool_properties,
    display_settings_properties,
    global_color_settings_properties,
    random_color_tool_properties,
    simple_fill_tool_properties,
    smooth_tool_properties,
    symmetrize_tool_properties,
)

classes = [
    random_color_tool_properties.RandomColorToolProperties,
    global_color_settings_properties.GlobalColorSettingsProperties,
    color_by_position_tool_properties.ColorByPositionToolProperties,
    simple_fill_tool_properties.SimpleFillToolProperties,
    display_settings_properties.DisplaySettingsProperties,
    smooth_tool_properties.SmoothToolProperties,
    color_by_selection_tool_properties.ColorBySelectionToolProperties,
    color_adjustments_tool_properties.ColorAdjustmentsToolProperties,
    attribute_transfer_tool_properties.AttributeTransferToolProperties,
    symmetrize_tool_properties.SymmetrizeToolProperties,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.hue_random_color_tool = bpy.props.PointerProperty(
        type=random_color_tool_properties.RandomColorToolProperties)
    bpy.types.Scene.hue_global_color_settings = bpy.props.PointerProperty(
        type=global_color_settings_properties.GlobalColorSettingsProperties)
    bpy.types.Scene.hue_color_by_position_tool = bpy.props.PointerProperty(
        type=color_by_position_tool_properties.ColorByPositionToolProperties)
    bpy.types.Scene.hue_simple_fill_tool = bpy.props.PointerProperty(
        type=simple_fill_tool_properties.SimpleFillToolProperties)
    bpy.types.Scene.hue_display_settings = bpy.props.PointerProperty(
        type=display_settings_properties.DisplaySettingsProperties)
    bpy.types.Scene.hue_smooth_tool = bpy.props.PointerProperty(
        type=smooth_tool_properties.SmoothToolProperties)
    bpy.types.Scene.hue_color_by_selection_tool = bpy.props.PointerProperty(
        type=color_by_selection_tool_properties.ColorBySelectionToolProperties)
    bpy.types.Scene.hue_color_adjustments_tool = bpy.props.PointerProperty(
        type=color_adjustments_tool_properties.ColorAdjustmentsToolProperties)
    bpy.types.Scene.hue_attribute_transfer_tool = bpy.props.PointerProperty(
        type=attribute_transfer_tool_properties.AttributeTransferToolProperties)
    bpy.types.Scene.hue_symmetrize_tool = bpy.props.PointerProperty(
        type=symmetrize_tool_properties.SymmetrizeToolProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.hue_random_color_tool
    del bpy.types.Scene.hue_global_color_settings
    del bpy.types.Scene.hue_color_by_position_tool
    del bpy.types.Scene.hue_simple_fill_tool
    del bpy.types.Scene.hue_display_settings
    del bpy.types.Scene.hue_smooth_tool
    del bpy.types.Scene.hue_color_by_selection_tool
    del bpy.types.Scene.hue_color_adjustments_tool
    del bpy.types.Scene.hue_attribute_transfer_tool
    del bpy.types.Scene.hue_symmetrize_tool
