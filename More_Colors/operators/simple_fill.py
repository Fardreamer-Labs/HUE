# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode, get_masked_color, get_active_color_attribute
)
from .base_operators import BaseColorOperator, BaseOperator


def _apply_fill(obj, color, mask, select_mode):
    """Apply color fill using the mesh data API (requires object mode)."""
    color_attribute = get_active_color_attribute(obj)

    match color_attribute.domain:
        case "CORNER":
            vert_to_loops = build_vertex_loop_map(obj)

            # Point Selection
            if select_mode[0]:
                for vert in obj.data.vertices:
                    if vert.select:
                        for loop_index in vert_to_loops.get(vert.index, []):
                            data = color_attribute.data[loop_index]
                            data.color_srgb = get_masked_color(data.color_srgb, color, mask)

            # Edge Selection
            if select_mode[1]:
                for edge in obj.data.edges:
                    if edge.select:
                        for vert_index in edge.vertices:
                            for loop_index in vert_to_loops.get(vert_index, []):
                                data = color_attribute.data[loop_index]
                                data.color_srgb = get_masked_color(data.color_srgb, color, mask)

            # Face Selection
            if select_mode[2]:
                for poly in obj.data.polygons:
                    if poly.select:
                        for loop_index in poly.loop_indices:
                            data = color_attribute.data[loop_index]
                            data.color_srgb = get_masked_color(data.color_srgb, color, mask)

        # Since "point" domain stores colors only for vertices, we can
        # modify their color directly without worrying about selection mode
        case "POINT":
            for p in obj.data.vertices:
                if p.select:
                    data = color_attribute.data[p.index]
                    data.color_srgb = get_masked_color(data.color_srgb, color, mask)

    obj.data.update()


def execute_simple_fill(context):
    """Core simple fill logic, callable without an operator instance.

    Returns (success, message) tuple.
    """
    scene = context.scene
    global_color_settings = scene.more_colors_global_color_settings
    simple_fill_tool = scene.more_colors_simple_fill_tool
    mask = global_color_settings.get_mask()
    color = simple_fill_tool.selected_color
    select_mode = context.tool_settings.mesh_select_mode

    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue

        with ensure_object_mode(obj):
            _apply_fill(obj, color, mask, select_mode)

    return True, "Vertex colors assigned successfully!"


class MC_OT_simple_fill(BaseColorOperator):
    """Applies a selected color to selected object(s) or part of the mesh"""

    bl_label = "Apply Color"
    bl_idname = "morecolors.simple_fill"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success, msg = execute_simple_fill(context)
        if not success:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class MC_OT_add_preset_color(BaseOperator):
    """Saves the current active color as a new color preset"""

    bl_label = "Add Preset Color"
    bl_idname = "morecolors.add_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        simple_fill_tool = context.scene.more_colors_simple_fill_tool
        palette = simple_fill_tool.preset_palette
        if not palette:
            palette = bpy.data.palettes.get("MORECOLORS_SimpleFillPresets")
            if not palette:
                palette = bpy.data.palettes.new("MORECOLORS_SimpleFillPresets")
            simple_fill_tool.preset_palette = palette
        color = simple_fill_tool.selected_color
        new_color = palette.colors.new()
        new_color.color = (color[0], color[1], color[2])
        simple_fill_tool.active_preset_index = len(palette.colors) - 1
        return {"FINISHED"}


class MC_OT_remove_preset_color(BaseOperator):
    """Removes the currently selected color preset"""

    bl_label = "Remove Preset Color"
    bl_idname = "morecolors.remove_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        simple_fill_tool = context.scene.more_colors_simple_fill_tool
        palette = simple_fill_tool.preset_palette
        if not palette or len(palette.colors) == 0:
            self.report({"WARNING"}, "No preset colors to remove")
            return {"CANCELLED"}
        idx = simple_fill_tool.active_preset_index
        idx = min(idx, len(palette.colors) - 1)
        palette.colors.remove(palette.colors[idx])
        if len(palette.colors) > 0:
            simple_fill_tool.active_preset_index = min(idx, len(palette.colors) - 1)
        else:
            simple_fill_tool.active_preset_index = 0
        return {"FINISHED"}


class MC_OT_use_preset_color(BaseOperator):
    """Selects this preset and sets it as the active color"""

    bl_label = "Use Preset Color"
    bl_idname = "morecolors.use_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        simple_fill_tool = context.scene.more_colors_simple_fill_tool
        palette = simple_fill_tool.preset_palette
        if not palette or self.index >= len(palette.colors):
            return {"CANCELLED"}
        color = palette.colors[self.index].color
        simple_fill_tool.selected_color[0] = color[0]
        simple_fill_tool.selected_color[1] = color[1]
        simple_fill_tool.selected_color[2] = color[2]
        simple_fill_tool.active_preset_index = self.index
        return {"FINISHED"}
