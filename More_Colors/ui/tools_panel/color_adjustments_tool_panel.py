# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_color_adjustments_tool_panel(BasePanelInfo, Panel):
    bl_label = "Color Adjustments"
    bl_idname = "MC_PT_color_adjustments_tool_panel"
    bl_parent_id = "MC_PT_adjust_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        tool = context.scene.more_colors_color_adjustments_tool

        layout.prop(tool, "operation")

        match tool.operation:
            case "LEVELS":
                col = layout.column(align=True)
                col.label(text="Input:")
                col.prop(tool, "levels_input_black", slider=True)
                col.prop(tool, "levels_input_white", slider=True)
                col.prop(tool, "levels_gamma", slider=True)
                col.separator()
                col.label(text="Output:")
                col.prop(tool, "levels_output_black", slider=True)
                col.prop(tool, "levels_output_white", slider=True)

            case "BRIGHTNESS_CONTRAST":
                layout.prop(tool, "brightness", slider=True)
                layout.prop(tool, "contrast", slider=True)

            case "HUE_SATURATION":
                layout.prop(tool, "hue_shift", slider=True)
                layout.prop(tool, "saturation", slider=True)
                layout.prop(tool, "value_adjust", slider=True)

            case "INVERT":
                layout.label(text="Inverts active mask channels.", icon="INFO")

            case "POSTERIZE":
                layout.prop(tool, "posterize_levels")

            case "BLEND":
                layout.prop_search(
                    tool, "blend_layer",
                    context.active_object.data, "color_attributes",
                    text="Layer",
                )
                layout.prop(tool, "blend_mode")
                layout.prop(tool, "blend_factor", slider=True)

        layout.separator()

        layout.operator("morecolors.color_adjustments", icon="BRUSH_DATA")
