# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo
from ...utilities.palette_utilities import (
    SWATCH_COLS, ensure_palette_assigned, get_color_icon,
)


class HUE_PT_random_color_tool_panel(BasePanelInfo, Panel):
    bl_label = "Randomize"
    bl_idname = "HUE_PT_random_color_tool_panel"
    bl_parent_id = "HUE_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 1

    def draw(self, context):
        layout = self.layout

        random_color_tool = context.scene.hue_random_color_tool

        mesh_count = sum(1 for obj in context.selected_objects if obj.type == "MESH")
        show_element_type = True
        obj = context.active_object

        if obj is not None and mesh_count <= 1:
            color_attribute = obj.data.color_attributes.active_color

            if color_attribute is not None:
                if color_attribute.domain == "POINT":
                    show_element_type = False

        if show_element_type:
            row = layout.row()
            row.prop(random_color_tool, "element_type")

        else:
            row = layout.row()
            row.label(
                text="Active color attribute uses Point domain."
                " Switch to Face Corner domain to choose element type.",
                icon="INFO")

        row = layout.row()
        row.label(text="Color Generation Method:")
        row.prop(random_color_tool, "color_mode", expand=True)

        if random_color_tool.color_mode == "Palette":
            ensure_palette_assigned(random_color_tool, "random_palette")
            box = layout.box()
            box.label(text="Palette", icon="COLOR")
            row = box.row(align=True)
            row.prop(random_color_tool, "random_palette", text="")

            palette = random_color_tool.random_palette
            if palette and len(palette.colors) > 0:
                for i, pc in enumerate(palette.colors):
                    if i % SWATCH_COLS == 0:
                        row = box.row(align=True)
                        row.alignment = 'LEFT'
                    icon_id = get_color_icon(*pc.color)
                    row.label(text="", icon_value=icon_id)

        row = layout.row()
        row.operator("hue.add_random_color", icon="SHADERFX")
