# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_color_by_position_tool_panel(BasePanelInfo, Panel):
    bl_label = "Gradient"
    bl_idname = "MC_PT_color_by_position_tool_panel"
    bl_parent_id = "MC_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        tool = context.scene.more_colors_color_by_position_tool

        layout.prop(tool, "gradient_source")

        match tool.gradient_source:
            case "POSITION":
                row = layout.row()
                row.label(text="Space:")
                row.prop(tool, "space_type", expand=True)
                layout.prop(tool, "gradient_direction")

            case "DISTANCE":
                row = layout.row()
                row.label(text="Space:")
                row.prop(tool, "space_type", expand=True)
                layout.prop(tool, "distance_origin")

            case "NOISE":
                row = layout.row()
                row.label(text="Space:")
                row.prop(tool, "space_type", expand=True)
                layout.prop(tool, "noise_scale")
                layout.prop(tool, "noise_detail")
                layout.prop(tool, "noise_seed")

            case "CURVATURE":
                pass

            case "WEIGHT":
                obj = context.active_object
                if obj and obj.type == "MESH" and obj.vertex_groups.active:
                    layout.label(
                        text=f"Group: {obj.vertex_groups.active.name}",
                        icon="GROUP_VERTEX",
                    )
                else:
                    layout.label(text="No active vertex group.", icon="INFO")

        material = bpy.data.materials.get(tool.color_ramp_material_name)
        if material is not None:
            node = material.node_tree.nodes['Color Ramp']
            layout.template_color_ramp(node, "color_ramp")

        layout.separator()

        layout.operator("morecolors.add_color_by_position", icon="BRUSH_DATA")
        layout.operator("morecolors.reset_color_by_position_gradient", icon="TRASH")
