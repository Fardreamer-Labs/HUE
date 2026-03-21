# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_color_by_selection_tool_panel(BasePanelInfo, Panel):
    bl_label = "Selection"
    bl_idname = "MC_PT_color_by_selection_tool_panel"
    bl_parent_id = "MC_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 4

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        tool = context.scene.more_colors_color_by_selection_tool

        row = layout.row(align=True)
        row.prop(tool, "selected_color", text="Selected")

        row = layout.row(align=True)
        row.prop(tool, "unselected_color", text="Unselected")

        layout.separator()

        layout.operator("morecolors.color_by_selection", icon="RESTRICT_SELECT_OFF")
