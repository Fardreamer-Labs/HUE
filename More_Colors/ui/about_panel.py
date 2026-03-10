# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import tomllib
from pathlib import Path

from bpy.types import Panel

from .base_panel_info import BasePanelInfo


def _get_version():
    manifest = Path(__file__).parent.parent / "blender_manifest.toml"
    with open(manifest, "rb") as f:
        data = tomllib.load(f)
    return data.get("version", "unknown")


class MC_PT_about_panel(BasePanelInfo, Panel):
    bl_label = "About"
    bl_idname = "MC_PT_about_panel"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text=f"More Colors! v{_get_version()}")

        row = layout.row()
        row.label(text="Made with love by Kai Fardreamer", icon="FUND")

        row = layout.row()
        row.operator("morecolors.open_documentation", icon="HELP")
