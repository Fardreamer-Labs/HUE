# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class MC_PT_tools_panel(BasePanelInfo, Panel):
    bl_label = "Tools"
    bl_idname = "MC_PT_tools_panel"
    bl_order = 0

    def draw(self, context):
        self.layout.operator("morecolors.open_documentation", icon="HELP")
