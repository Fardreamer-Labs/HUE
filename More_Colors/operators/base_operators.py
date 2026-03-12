# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator

from ..utilities.color_utilities import is_vertex_color_visible

_ROOT_PKG = __package__.rsplit('.', 1)[0]


class BaseOperator(Operator):
    bl_label = ""


class BaseColorOperator(BaseOperator):
    """Base operator for vertex color operations.

    Contains a poll method that prevents using the operator when no mesh is selected.
    """

    warn_visibility_check = True

    @classmethod
    def poll(cls, context):
        return any(obj.type == "MESH" for obj in context.selected_objects)

    def invoke(self, context, event):
        result = self.execute(context)
        if result == {'FINISHED'}:
            self._maybe_warn_visibility(context)
        return result

    def _maybe_warn_visibility(self, context):
        if not self.warn_visibility_check:
            return
        try:
            prefs = bpy.context.preferences.addons[_ROOT_PKG].preferences
        except KeyError:
            return
        if prefs.suppress_visibility_warning:
            return
        if is_vertex_color_visible(context):
            return
        bpy.app.timers.register(
            lambda: bpy.ops.morecolors.visibility_warning('INVOKE_DEFAULT'),
            first_interval=0,
        )
