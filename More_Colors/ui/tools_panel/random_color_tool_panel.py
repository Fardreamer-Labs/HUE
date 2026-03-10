# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_random_color_tool_panel(BasePanelInfo, Panel):
    bl_label = "Random Color Per Element"
    bl_idname = "MC_PT_random_color_tool_panel"
    bl_parent_id = "MC_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 1

    def draw(self, context):
        layout = self.layout

        random_color_tool = context.scene.more_colors_random_color_tool

        show_element_type = True
        obj = context.active_object

        if obj is not None:
            color_attribute = obj.data.color_attributes.active_color

            if color_attribute is not None:
                if color_attribute.domain == "POINT":
                    show_element_type = False

        if show_element_type:
            row = layout.row()
            row.label(text="Applies a random vertex color per selected element.")

            row = layout.row()
            row.prop(random_color_tool, "element_type")

        else:
            row = layout.row()
            row.label(text="Applies a random vertex color per each point.")

            row = layout.row()
            row.label(
                text="If you want to select the element you're applying a random color to,"
                " select a color attribute with a \"Face Corner\" domain!",
                icon="INFO")

        row = layout.row()
        row.label(text="Color Generation Method:")
        row.prop(random_color_tool, "color_mode", expand=True)

        if random_color_tool.color_mode == "Palette":
            row = layout.row()
            row.label(text="Palette", icon="COLOR")

            column = layout.column(align=True)
            split = column.split()

            row = split.row()
            row.prop(random_color_tool, "palette_color_1", text="")

            row = split.row()
            row.prop(random_color_tool, "palette_color_2", text="")

            row = split.row()
            row.prop(random_color_tool, "palette_color_3", text="")

            row = split.row()
            row.prop(random_color_tool, "palette_color_4", text="")

        row = layout.row()
        row.operator("morecolors.add_random_color", icon="SHADERFX")
