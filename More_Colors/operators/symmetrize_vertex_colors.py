# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
from mathutils.kdtree import KDTree

from ..utilities.color_utilities import (
    apply_mask_array, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute,
    get_selected_color_indices,
)
from .base_operators import BaseColorOperator


class MC_OT_symmetrize_vertex_colors(BaseColorOperator):
    """Mirror vertex colors across an axis"""

    bl_label = "Symmetrize Vertex Colors"
    bl_idname = "morecolors.symmetrize_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        tool = scene.more_colors_symmetrize_tool
        mask = scene.more_colors_global_color_settings.get_mask()
        in_edit = context.mode == 'EDIT_MESH'
        select_mode = context.tool_settings.mesh_select_mode if in_edit else None

        axis_index = {"X": 0, "Y": 1, "Z": 2}[tool.axis]

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                self._symmetrize_object(
                    obj, axis_index, tool.direction, tool.threshold,
                    mask, select_mode,
                )

        self.report({"INFO"}, "Vertex colors symmetrized!")
        return {"FINISHED"}

    @staticmethod
    def _symmetrize_object(obj, axis_index, direction, threshold, mask, select_mode):
        mesh = obj.data
        color_attribute = get_active_color_attribute(obj)
        num_verts = len(mesh.vertices)

        # Load vertex positions
        coords = np.empty(num_verts * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", coords)
        coords = coords.reshape(num_verts, 3)

        # Build KDTree from all vertices
        tree = KDTree(num_verts)
        for i in range(num_verts):
            tree.insert(coords[i], i)
        tree.balance()

        # Determine source/destination based on direction
        # POSITIVE_TO_NEGATIVE: +side is source, -side receives
        # NEGATIVE_TO_POSITIVE: -side is source, +side receives
        if direction == "POSITIVE_TO_NEGATIVE":
            source_mask = coords[:, axis_index] >= 0
        else:
            source_mask = coords[:, axis_index] <= 0

        # Load colors
        all_colors = bulk_get_colors(color_attribute)

        if color_attribute.domain == "CORNER":
            n_loops = len(mesh.loops)
            loop_verts = np.empty(n_loops, dtype=np.int32)
            mesh.loops.foreach_get("vertex_index", loop_verts)

            # Average loop colors per vertex
            vert_colors = np.zeros((num_verts, 4), dtype=np.float32)
            loop_count = np.zeros(num_verts, dtype=np.float32)
            np.add.at(vert_colors, loop_verts, all_colors)
            np.add.at(loop_count, loop_verts, 1)
            loop_count = np.maximum(loop_count, 1)
            vert_colors /= loop_count[:, np.newaxis]
        else:
            loop_verts = None
            vert_colors = all_colors.copy()

        # Build mirror mapping: for each destination vertex, find source vertex
        new_vert_colors = vert_colors.copy()
        for vi in range(num_verts):
            if source_mask[vi]:
                continue  # This vertex is on the source side, skip

            # Compute mirror position
            mirror_pos = coords[vi].copy()
            mirror_pos[axis_index] = -mirror_pos[axis_index]

            # Find nearest vertex to mirror position
            co, idx, dist = tree.find(mirror_pos)
            if dist <= threshold and source_mask[idx]:
                new_vert_colors[vi] = vert_colors[idx]

        # Apply selection filter
        if color_attribute.domain == "CORNER":
            new_loop_colors = new_vert_colors[loop_verts]
            indices = get_selected_color_indices(obj, select_mode, "CORNER")
            if indices is not None:
                filtered = all_colors.copy()
                filtered[indices] = new_loop_colors[indices]
                apply_mask_array(all_colors, filtered, mask)
            else:
                apply_mask_array(all_colors, new_loop_colors, mask)
        else:
            indices = get_selected_color_indices(obj, select_mode, "POINT")
            if indices is not None:
                filtered = vert_colors.copy()
                filtered[indices] = new_vert_colors[indices]
                apply_mask_array(all_colors, filtered, mask)
            else:
                apply_mask_array(all_colors, new_vert_colors, mask)

        bulk_set_colors(color_attribute, all_colors)
        mesh.update()
