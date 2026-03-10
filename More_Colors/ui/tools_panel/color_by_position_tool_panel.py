# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_color_by_position_tool_panel(BasePanelInfo, Panel):
    bl_label = "Color By Position"
    bl_idname = "MC_PT_color_by_position_tool_panel"
    bl_parent_id = "MC_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 2

    def draw(self, context):
        layout = self.layout

        color_by_position_tool = context.scene.more_colors_color_by_position_tool

        # If there is no color ramp material, ask the user to initialize
        if bpy.data.materials.get(color_by_position_tool.color_ramp_material_name) is None:
            row = layout.row()
            row.operator("morecolors.initialize_color_by_position_tool", icon="TOOL_SETTINGS")

        # Draw the tool
        else:
            row = layout.row()
            row.label(text="Applies a position-based vertex color.")

            row = layout.row()
            row.label(text="Space Type:")
            row.prop(color_by_position_tool, "space_type", expand=True)

            row = layout.row()
            row.prop(color_by_position_tool, "gradient_direction")

            material = bpy.data.materials.get(color_by_position_tool.color_ramp_material_name)
            node = material.node_tree.nodes['Color Ramp']
            layout.template_color_ramp(node, "color_ramp")

            layout.row()

            row = layout.row()
            row.operator("morecolors.add_color_by_position", icon="BRUSH_DATA")

            row = layout.row()
            row.operator("morecolors.reset_color_by_position_gradient", icon="TRASH")
