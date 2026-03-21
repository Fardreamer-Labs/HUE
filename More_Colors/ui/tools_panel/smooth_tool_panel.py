# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_smooth_tool_panel(BasePanelInfo, Panel):
    bl_label = "Smooth"
    bl_idname = "MC_PT_smooth_tool_panel"
    bl_parent_id = "MC_PT_adjust_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        tool = context.scene.more_colors_smooth_tool

        layout.prop(tool, "constraint_mode")
        layout.prop(tool, "iterations")
        layout.prop(tool, "factor", slider=True)

        layout.separator()

        layout.operator("morecolors.smooth_vertex_colors", icon="SMOOTHCURVE")
