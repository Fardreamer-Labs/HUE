# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..utilities.color_utilities import get_masked_color, get_active_color_attribute
from .base_operators import BaseColorOperator


def _apply_fill(obj, color, mask, select_mode):
    """Apply color fill using the mesh data API (requires object mode)."""
    color_attribute = get_active_color_attribute(obj)

    match color_attribute.domain:
        case "CORNER":
            # Build vertex -> loop indices map in O(L)
            vert_to_loops = {}
            for loop in obj.data.loops:
                vert_to_loops.setdefault(loop.vertex_index, []).append(loop.index)

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
    if not context.selected_objects:
        return False, "No objects selected!"

    scene = context.scene
    global_color_settings = scene.more_colors_global_color_settings
    simple_fill_tool = scene.more_colors_simple_fill_tool
    mask = global_color_settings.get_mask()
    color = simple_fill_tool.selected_color
    select_mode = context.tool_settings.mesh_select_mode

    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue

        # Mesh data API requires object mode; switch back after if needed
        was_in_edit_mode = (obj.mode == "EDIT")
        if was_in_edit_mode:
            bpy.ops.object.mode_set(mode="OBJECT")

        _apply_fill(obj, color, mask, select_mode)

        if was_in_edit_mode:
            bpy.ops.object.mode_set(mode="EDIT")

    return True, "Vertex colors assigned successfully!"


class MC_OT_simple_fill(BaseColorOperator):
    """Applies a selected color to selected object(s) or part of the mesh"""

    bl_label = "Apply"
    bl_idname = "morecolors.simple_fill"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success, msg = execute_simple_fill(context)
        if not success:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class MC_OT_select_preset_color(bpy.types.Operator):
    """Selects the preset's color"""

    bl_label = "Select"
    bl_idname = "morecolors.select_preset_color"

    preset_name: bpy.props.StringProperty(options={"HIDDEN"})

    def execute(self, context):
        simple_fill_tool = context.scene.more_colors_simple_fill_tool
        simple_fill_tool.selected_color = getattr(simple_fill_tool, self.preset_name)

        return {"FINISHED"}


class MC_OT_apply_preset_color(BaseColorOperator):
    """Applies the preset color to selected object(s) or part of the mesh"""

    bl_label = "Quick Apply"
    bl_idname = "morecolors.apply_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name: bpy.props.StringProperty(options={"HIDDEN"})

    def execute(self, context):
        simple_fill_tool = context.scene.more_colors_simple_fill_tool

        # Copy the color data, instead of creating a reference
        previous_selected_color = list(simple_fill_tool.selected_color)

        simple_fill_tool.selected_color = getattr(simple_fill_tool, self.preset_name)
        execute_simple_fill(context)
        simple_fill_tool.selected_color = previous_selected_color

        return {"FINISHED"}
