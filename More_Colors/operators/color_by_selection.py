# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np

from ..utilities.color_utilities import (
    apply_mask_constant, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute, get_selected_color_indices,
)
from .base_operators import BaseColorOperator


class MC_OT_color_by_selection(BaseColorOperator):
    """Colors selected elements one color and unselected another"""

    bl_label = "Color By Selection"
    bl_idname = "morecolors.color_by_selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool = context.scene.more_colors_color_by_selection_tool
        mask = context.scene.more_colors_global_color_settings.get_mask()
        sel_color = tool.selected_color
        unsel_color = tool.unselected_color
        select_mode = context.tool_settings.mesh_select_mode

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                self._apply(obj, sel_color, unsel_color, mask, select_mode)

        self.report({"INFO"}, "Selection colors applied!")
        return {"FINISHED"}

    @staticmethod
    def _apply(obj, sel_color, unsel_color, mask, select_mode):
        color_attribute = get_active_color_attribute(obj)
        # Face mode takes priority (matches original behavior)
        effective_mode = (False, False, True) if select_mode[2] else select_mode
        selected = get_selected_color_indices(obj, effective_mode, color_attribute.domain)

        colors = bulk_get_colors(color_attribute)
        n = len(colors)
        unselected = np.setdiff1d(np.arange(n, dtype=np.intp), selected)

        apply_mask_constant(colors, sel_color, mask, selected)
        apply_mask_constant(colors, unsel_color, mask, unselected)

        bulk_set_colors(color_attribute, colors)
        obj.data.update()
