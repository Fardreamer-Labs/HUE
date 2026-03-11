# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_display_settings_panel(BasePanelInfo, Panel):
    bl_label = "Viewport Display"
    bl_idname = "MC_PT_display_settings_panel"
    bl_parent_id = "MC_PT_settings_panel"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        display_settings = context.scene.more_colors_display_settings

        obj = context.object
        has_mesh = obj is not None and obj.type == "MESH" and obj.mode != "VERTEX_PAINT"

        col = layout.column()
        col.enabled = has_mesh
        col.prop(display_settings, "display_mode", expand=True)

        if has_mesh and display_settings.display_mode == "Alpha":
            layout.label(text="Alpha mode overrides active object materials.", icon="INFO")
