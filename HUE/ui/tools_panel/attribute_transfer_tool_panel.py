# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class HUE_PT_attribute_transfer_tool_panel(BasePanelInfo, Panel):
    bl_label = "Attribute Transfer"
    bl_idname = "HUE_PT_attribute_transfer_tool_panel"
    bl_parent_id = "HUE_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    def draw(self, context):
        layout = self.layout
        tool = context.scene.hue_attribute_transfer_tool

        layout.prop(tool, "source_object")

        if tool.source_object is not None:
            layout.prop_search(
                tool, "source_layer",
                tool.source_object.data, "color_attributes",
                text="Source Layer",
            )

        layout.prop(tool, "transfer_mode")
        layout.prop(tool, "mix_factor", slider=True)

        layout.separator()

        layout.operator("hue.attribute_transfer", icon="BRUSH_DATA")
