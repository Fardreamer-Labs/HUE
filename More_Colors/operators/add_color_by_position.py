# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .base_operators import BaseColorOperator, BaseOperator
from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode, get_masked_color, get_active_color_attribute
)


class MC_OT_add_color_by_position(BaseColorOperator):
    """Adds a color based on vertex position for each selected mesh object"""

    bl_label = "Add Color By Position"
    bl_idname = "morecolors.add_color_by_position"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        global_color_settings = scene.more_colors_global_color_settings
        color_by_position_tool = scene.more_colors_color_by_position_tool

        gradient_direction = color_by_position_tool.gradient_direction
        axis_index = {"X": 0, "Y": 1, "Z": 2}[gradient_direction[-1]]

        # Reverse direction names always have more than one letter in the name
        reverse_gradient = len(gradient_direction) > 1

        color_ramp = self.get_color_ramp(context)
        mask = global_color_settings.get_mask()

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)

                vertex_positions = [
                    obj.matrix_world @ v.co if color_by_position_tool.space_type == "World" else v.co
                    for v in obj.data.vertices
                ]

                # Calculate min and max based on the axis
                positions_along_axis = [pos[axis_index] for pos in vertex_positions]
                min_pos = min(positions_along_axis)
                max_pos = max(positions_along_axis)

                pos_range = max_pos - min_pos
                if pos_range == 0:
                    pos_range = 1  # Avoid division by zero; all vertices get position 0

                match color_attribute.domain:
                    case "CORNER":
                        vert_to_loops = build_vertex_loop_map(obj)

                        for vert in obj.data.vertices:
                            pos_value = vertex_positions[vert.index][axis_index]
                            gradient_position = (pos_value - min_pos) / pos_range

                            if reverse_gradient:
                                gradient_position = 1 - gradient_position

                            color = color_ramp.evaluate(gradient_position)

                            for loop_index in vert_to_loops.get(vert.index, []):
                                data = color_attribute.data[loop_index]
                                data.color_srgb = get_masked_color(data.color_srgb, color, mask)

                    case "POINT":
                        for vert in obj.data.vertices:
                            pos_value = vertex_positions[vert.index][axis_index]
                            gradient_position = (pos_value - min_pos) / pos_range

                            if reverse_gradient:
                                gradient_position = 1 - gradient_position

                            color = color_ramp.evaluate(gradient_position)

                            data = color_attribute.data[vert.index]
                            data.color_srgb = get_masked_color(data.color_srgb, color, mask)

                obj.data.update()

        self.report({"INFO"}, "Vertex colors assigned successfully!")
        return {"FINISHED"}

    def get_color_ramp(self, context):
        color_by_position_tool = context.scene.more_colors_color_by_position_tool
        material_name = color_by_position_tool.color_ramp_material_name
        material = bpy.data.materials.get(material_name)
        if material is None:
            material = bpy.data.materials.new(name=material_name)
            material.use_nodes = True
            nodes = material.node_tree.nodes
            nodes.clear()
            nodes.new(type="ShaderNodeValToRGB")
        node = material.node_tree.nodes["Color Ramp"]
        return node.color_ramp


class MC_OT_reset_color_by_position_gradient(BaseOperator):
    """Resets the gradient to a default black and white value"""

    bl_label = "Reset Gradient"
    bl_idname = "morecolors.reset_color_by_position_gradient"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        color_by_position_tool = context.scene.more_colors_color_by_position_tool
        material_name = color_by_position_tool.color_ramp_material_name

        material = bpy.data.materials.get(material_name)
        if material is None:
            self.report({"ERROR"}, "No gradient to reset.")
            return {"CANCELLED"}

        node = material.node_tree.nodes["Color Ramp"]
        color_ramp = node.color_ramp

        # Color Ramp node needs at least one element, so we don't delete the first one
        while len(color_ramp.elements) > 1:
            color_ramp.elements.remove(color_ramp.elements[0])

        black = node.color_ramp.elements[0]
        black.position = 0
        black.color = (0, 0, 0, 1)

        white = node.color_ramp.elements.new(1)
        white.color = (1, 1, 1, 1)

        return {"FINISHED"}
