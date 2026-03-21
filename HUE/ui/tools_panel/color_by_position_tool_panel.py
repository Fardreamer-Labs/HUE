# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class HUE_PT_color_by_position_tool_panel(BasePanelInfo, Panel):
    bl_label = "Gradient"
    bl_idname = "HUE_PT_color_by_position_tool_panel"
    bl_parent_id = "HUE_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        tool = context.scene.hue_color_by_position_tool

        layout.prop(tool, "gradient_source")

        match tool.gradient_source:
            case "POSITION":
                row = layout.row()
                row.label(text="Space:")
                row.prop(tool, "space_type", expand=True)
                layout.prop(tool, "gradient_direction")

            case "DISTANCE":
                layout.prop(tool, "distance_origin")

            case "NOISE":
                row = layout.row()
                row.label(text="Space:")
                row.prop(tool, "space_type", expand=True)
                layout.prop(tool, "noise_scale")
                layout.prop(tool, "noise_detail")
                layout.prop(tool, "noise_basis")

                header, body = layout.panel(
                    "HUE_PT_noise_advanced", default_closed=True
                )
                header.label(text="Advanced")
                if body:
                    body.prop(tool, "noise_type")
                    body.prop(tool, "noise_roughness")
                    body.prop(tool, "noise_lacunarity")
                    body.prop(tool, "noise_distortion")
                    body.prop(tool, "noise_seed")

            case "CURVATURE":
                layout.prop(tool, "curvature_use_cotangent")

            case "DIRTY":
                layout.prop(tool, "dirt_highlight_angle")
                layout.prop(tool, "dirt_dirt_angle")
                layout.prop(tool, "dirt_blur_iterations")
                layout.prop(tool, "dirt_blur_strength")
                layout.prop(tool, "dirt_only_dirty")
                layout.prop(tool, "dirt_normalize")

            case "WEIGHT":
                obj = context.active_object
                if obj and obj.type == "MESH" and obj.vertex_groups.active:
                    layout.label(
                        text=f"Group: {obj.vertex_groups.active.name}",
                        icon="GROUP_VERTEX",
                    )
                else:
                    layout.label(text="No active vertex group.", icon="INFO")

            case "VALENCE" | "FACE_AREA" | "EDGE_LENGTH_VAR" | "FACE_QUALITY":
                pass

        layout.prop(tool, "normalize_per_island")

        material = bpy.data.materials.get(tool.color_ramp_material_name)
        if material is not None:
            node = material.node_tree.nodes['Color Ramp']
            layout.template_color_ramp(node, "color_ramp")

        layout.separator()

        layout.operator("hue.add_color_by_position", icon="BRUSH_DATA")
        layout.operator("hue.reset_color_by_position_gradient", icon="TRASH")
