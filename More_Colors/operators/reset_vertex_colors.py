# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..utilities.color_utilities import get_active_color_attribute
from .base_operators import BaseColorOperator


class MC_OT_reset_color(BaseColorOperator):
    """Resets all vertex colors to white"""

    bl_label = "Reset Vertex Colors"
    bl_idname = "morecolors.reset_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            was_in_edit_mode = (obj.mode == "EDIT")
            if was_in_edit_mode:
                bpy.ops.object.mode_set(mode="OBJECT")

            color_attribute = get_active_color_attribute(obj)

            for data in color_attribute.data:
                data.color_srgb = (1, 1, 1, 1)

            obj.data.update()

            if was_in_edit_mode:
                bpy.ops.object.mode_set(mode="EDIT")

        self.report({"INFO"}, "Vertex colors have been reset!")
        return {"FINISHED"}
