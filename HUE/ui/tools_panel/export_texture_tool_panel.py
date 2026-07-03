# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class HUE_PT_export_texture_tool_panel(BasePanelInfo, Panel):
    bl_label = "Make Texture"
    bl_idname = "HUE_PT_export_texture_tool_panel"
    bl_parent_id = "HUE_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 6

    def draw(self, context):
        layout = self.layout
        tool = context.scene.hue_export_texture_tool
        obj = context.active_object

        layout.prop(tool, "export_name")

        row = layout.row(align=True)
        row.prop(tool, "resolution_x")
        row.prop(
            tool,
            "resolution_linked",
            icon="LINKED" if tool.resolution_linked else "UNLINKED",
            icon_only=True,
            toggle=True,
        )
        row.prop(tool, "resolution_y")

        layout.prop(tool, "margin")
        layout.prop(tool, "color_depth")
        layout.prop(tool, "colorspace")
        layout.prop(tool, "auto_unwrap")
        layout.prop(tool, "apply_material")

        if (
            not tool.auto_unwrap
            and obj is not None
            and obj.type == "MESH"
            and obj.data.uv_layers.active is None
        ):
            layout.label(text="No UV layer — enable Auto Unwrap or add one manually", icon="ERROR")

        layout.separator()
        layout.operator("hue.make_texture", icon="TEXTURE")

        layout.separator()
        if tool.generated_image_name in bpy.data.images:
            img = bpy.data.images[tool.generated_image_name]
            row = layout.row()
            row.template_icon(icon_value=img.preview_ensure().icon_id, scale=3.0)
            row.label(text=f"Texture: {img.name}")
        else:
            layout.label(text="No texture created yet", icon="IMAGE_DATA")
        layout.prop(tool, "export_path")
        layout.prop(tool, "overwrite_existing")
        layout.operator("hue.export_color_attribute", icon="EXPORT")
