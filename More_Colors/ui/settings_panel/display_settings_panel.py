# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_display_settings_panel(BasePanelInfo, Panel):
    bl_label = "Display Settings"
    bl_idname = "MC_PT_display_settings_panel"
    bl_parent_id = "MC_PT_settings_panel"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        display_settings = context.scene.more_colors_display_settings

        if context.object and context.object.type == "MESH":
            if context.object.mode != "VERTEX_PAINT":
                row = layout.row()
                row.label(text="Vertex colors display mode:", icon="MESH_DATA")

                row = layout.row()
                row.prop(display_settings, "display_mode", expand=True)

                row = layout.row()
                row.label(
                    text="Alpha display mode will temporary override the active object's materials!",
                    icon="ERROR")

                row = layout.row()
                row.label(
                    text="Don't forget to re-enable alpha display mode if you've selected"
                    " a different object or color attribute.",
                    icon="INFO")

            else:
                row = layout.row()
                row.label(text="Enter object mode!", icon="ERROR")

        elif context.object:
            row = layout.row()
            row.label(text="Active object is not mesh!", icon="ERROR")

        else:
            row = layout.row()
            row.label(text="No active object!", icon="ERROR")
