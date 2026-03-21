# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class HUE_PT_adjust_panel(BasePanelInfo, Panel):
    bl_label = "Adjust"
    bl_idname = "HUE_PT_adjust_panel"
    bl_parent_id = "HUE_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3

    def draw(self, context):
        pass
