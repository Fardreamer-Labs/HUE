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
    bl_order = 99
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.label(text=f"More Colors! v{_get_version()}")

        col = layout.column(align=True)
        col.label(text="Created by Kai Fardreamer", icon="FUND")
        col.label(text="Maintained by Clonephaze", icon="FUND")
