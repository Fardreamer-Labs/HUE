# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np

from ..utilities.color_utilities import (
    bulk_get_colors, bulk_set_colors, ensure_object_mode,
    get_active_color_attribute, get_selected_color_indices,
)
from .base_operators import BaseColorOperator


class HUE_OT_reset_color(BaseColorOperator):
    """Resets vertex colors to white (selection-aware in edit mode)"""

    warn_visibility_check = False

    bl_label = "Reset Vertex Colors"
    bl_idname = "hue.reset_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        select_mode = context.tool_settings.mesh_select_mode if context.mode == 'EDIT_MESH' else None

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)
                self._reset_colors(obj, color_attribute, select_mode)
                obj.data.update()

        self.report({"INFO"}, "Vertex colors have been reset!")
        return {"FINISHED"}

    @staticmethod
    def _reset_colors(obj, color_attribute, select_mode):
        indices = get_selected_color_indices(obj, select_mode, color_attribute.domain)

        if indices is None:
            # Object mode: set all to white
            n = len(color_attribute.data)
            bulk_set_colors(color_attribute, np.ones((n, 4), dtype=np.float32))
            return

        if len(indices) == 0:
            return

        colors = bulk_get_colors(color_attribute)
        colors[indices] = 1.0
        bulk_set_colors(color_attribute, colors)
