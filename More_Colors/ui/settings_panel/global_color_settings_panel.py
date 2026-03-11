# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_global_color_settings_panel(BasePanelInfo, Panel):
    bl_label = "Color Mask"
    bl_idname = "MC_PT_global_color_settings_panel"
    bl_parent_id = "MC_PT_settings_panel"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        tool = context.scene.more_colors_global_color_settings

        row = layout.row()
        row.label(text="Affected channels:", icon="COLOR")

        row = layout.row(align=True)
        row.prop(tool, "global_color_mask_r", text="R", toggle=True)
        row.prop(tool, "global_color_mask_g", text="G", toggle=True)
        row.prop(tool, "global_color_mask_b", text="B", toggle=True)
        row.prop(tool, "global_color_mask_a", text="A", toggle=True)

        layout.separator()

        # Reset Vertex Colors
        row = layout.row()
        row.operator("morecolors.reset_vertex_colors", icon="TRASH")
