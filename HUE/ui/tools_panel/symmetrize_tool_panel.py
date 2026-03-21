# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class HUE_PT_symmetrize_tool_panel(BasePanelInfo, Panel):
    bl_label = "Symmetrize"
    bl_idname = "HUE_PT_symmetrize_tool_panel"
    bl_parent_id = "HUE_PT_adjust_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        tool = context.scene.hue_symmetrize_tool

        layout.prop(tool, "axis")
        row = layout.row(align=True)
        row.prop(tool, "direction", expand=True)
        layout.prop(tool, "threshold")

        layout.separator()

        layout.operator("hue.symmetrize_vertex_colors", icon="MOD_MIRROR")
