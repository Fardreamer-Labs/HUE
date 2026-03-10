# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_simple_fill_tool_panel(BasePanelInfo, Panel):
    bl_label = "Simple Fill"
    bl_idname = "MC_PT_simple_fill_tool_panel"
    bl_parent_id = "MC_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 0

    def draw(self, context):
        layout = self.layout

        simple_fill_tool = context.scene.more_colors_simple_fill_tool

        row = layout.row()
        row.label(text="Fills a selection with color.")

        layout.separator()

        row = layout.row()
        row.label(text="Presets", icon="COLOR")

        column = layout.column(align=True)

        split = column.split()
        row = split.row()
        row.prop(simple_fill_tool, "preset_color_1", text="")
        split.operator("morecolors.select_preset_color", icon="EYEDROPPER").preset_name = "preset_color_1"
        split.operator("morecolors.apply_preset_color", icon="BRUSH_DATA").preset_name = "preset_color_1"

        split = column.split()
        row = split.row()
        row.prop(simple_fill_tool, "preset_color_2", text="")
        split.operator("morecolors.select_preset_color", icon="EYEDROPPER").preset_name = "preset_color_2"
        split.operator("morecolors.apply_preset_color", icon="BRUSH_DATA").preset_name = "preset_color_2"

        split = column.split()
        row = split.row()
        row.prop(simple_fill_tool, "preset_color_3", text="")
        split.operator("morecolors.select_preset_color", icon="EYEDROPPER").preset_name = "preset_color_3"
        split.operator("morecolors.apply_preset_color", icon="BRUSH_DATA").preset_name = "preset_color_3"

        split = column.split()
        row = split.row()
        row.prop(simple_fill_tool, "preset_color_4", text="")
        split.operator("morecolors.select_preset_color", icon="EYEDROPPER").preset_name = "preset_color_4"
        split.operator("morecolors.apply_preset_color", icon="BRUSH_DATA").preset_name = "preset_color_4"

        layout.separator()

        row = layout.row()
        row.prop(simple_fill_tool, "selected_color", text="")
        row.operator("morecolors.simple_fill", icon="BRUSH_DATA")
