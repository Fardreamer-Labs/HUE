# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_color_attributes_settings_panel(BasePanelInfo, Panel):
    bl_label = "Color Attributes Settings"
    bl_idname = "MC_PT_color_attributes_settings_panel"
    bl_parent_id = "MC_PT_settings_panel"
    bl_order = 2

    def draw(self, context):
        layout = self.layout

        if len(context.selected_objects) > 1:
            row = layout.row()
            row.label(
                text="Two or more objects selected, color attributes settings support only one object!",
                icon="ERROR")

        elif len(context.selected_objects) == 0:
            row = layout.row()
            row.label(text="No objects selected, select something!", icon="ERROR")

        elif context.active_object.type != "MESH":
            row = layout.row()
            row.label(text="Selected object is not a mesh!", icon="ERROR")

        else:
            mesh = context.active_object.data
            row = layout.row()

            col = row.column()
            col.template_list(
                "MESH_UL_color_attributes",
                "color_attributes",
                mesh,
                "color_attributes",
                mesh.color_attributes,
                "active_color_index",
                rows=3,
            )

            col = row.column(align=True)
            col.operator("geometry.color_attribute_add", icon='ADD', text="")
            col.operator("geometry.color_attribute_remove", icon='REMOVE', text="")

            col.separator()

            col.menu("MESH_MT_color_attribute_context_menu", icon='DOWNARROW_HLT', text="")
