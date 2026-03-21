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

        # --- Credits ---
        col = layout.column(align=True)
        col.label(text="Created by Kai Fardreamer")
        col.label(text="Major contributions by Clonephaze")

        layout.separator()

        # --- Links ---
        col = layout.column(align=True)
        col.operator("morecolors.open_documentation", text="Open Documentation", icon="HELP")
        col.operator("morecolors.open_bug_report", text="Report Bug / Request Feature", icon="SYSTEM")

        layout.separator()

        # --- Review ---
        box = layout.box()
        box.label(text="Enjoying More Colors?", icon="FUND")
        box.operator("morecolors.open_review", text="Leave a Review!", icon="SOLO_ON")
