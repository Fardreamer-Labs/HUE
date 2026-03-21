# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo
from ...utilities.palette_utilities import (
    SWATCH_COLS, ensure_palette_assigned, get_color_icon,
)


class MC_PT_simple_fill_tool_panel(BasePanelInfo, Panel):
    bl_label = "Fill"
    bl_idname = "MC_PT_simple_fill_tool_panel"
    bl_parent_id = "MC_PT_tools_panel"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        tool = context.scene.more_colors_simple_fill_tool
        ensure_palette_assigned(tool, "preset_palette")

        # --- Active color + apply button ---
        box = layout.box()
        box.label(text="Active Color", icon="BRUSH_DATA")
        row = box.row(align=True)
        row.prop(tool, "selected_color", text="")
        row.operator("morecolors.simple_fill", icon="CHECKMARK")

        layout.separator()

        # --- Palette selector ---
        box = layout.box()
        header_row = box.row(align=False)
        header_row.label(text="Color Presets", icon="COLOR")
        header_row.prop(tool, "quick_fill", text="Quick Fill", toggle=True, icon="PLAY")
        row = box.row(align=True)
        row.prop(tool, "preset_palette", text="")
        row.operator("morecolors.new_palette", icon="FILE_NEW", text="")
        if tool.preset_palette:
            row.operator("morecolors.rename_palette", icon="GREASEPENCIL", text="")
            row.operator("morecolors.delete_palette", icon="TRASH", text="")

        # --- Swatch grid ---
        palette = tool.preset_palette
        if palette and len(palette.colors) > 0:
            active_idx = tool.active_preset_index
            for i, pc in enumerate(palette.colors):
                if i % SWATCH_COLS == 0:
                    row = box.row(align=True)
                    row.alignment = 'LEFT'
                icon_id = get_color_icon(*pc.color)
                op = row.operator(
                    "morecolors.use_preset_color",
                    text="",
                    icon_value=icon_id,
                    depress=(i == active_idx),
                )
                op.index = i

        # --- Add / Remove buttons ---
        row = box.row(align=True)
        row.operator("morecolors.add_preset_color", icon="ADD", text="")
        if palette and len(palette.colors) > 0:
            row.operator("morecolors.remove_preset_color", icon="REMOVE", text="")
