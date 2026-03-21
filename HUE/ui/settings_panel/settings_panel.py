# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel

from ..base_panel_info import BasePanelInfo


class HUE_PT_settings_panel(BasePanelInfo, Panel):
    bl_label = "Settings"
    bl_idname = "HUE_PT_settings_panel"
    bl_order = 1

    def draw(self, context):
        pass
