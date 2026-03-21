# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np

from ..utilities.color_utilities import (
    apply_mask_array, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute,
)
from .base_operators import BaseColorOperator


class HUE_OT_smooth_vertex_colors(BaseColorOperator):
    """Smooths vertex colors by averaging with neighboring vertices"""

    bl_label = "Smooth Colors"
    bl_idname = "hue.smooth_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool = context.scene.hue_smooth_tool
        mask = context.scene.hue_global_color_settings.get_mask()

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                self._smooth_object(obj, tool.iterations, tool.factor, mask, tool.constraint_mode)

        self.report({"INFO"}, "Vertex colors smoothed!")
        return {"FINISHED"}

    @staticmethod
    def _smooth_object(obj, iterations, factor, mask, constraint_mode="NONE"):
        mesh = obj.data
        color_attribute = get_active_color_attribute(obj)
        num_verts = len(mesh.vertices)
        all_colors = bulk_get_colors(color_attribute)

        # Build edge pair arrays for vectorized neighbor accumulation
        n_edges = len(mesh.edges)
        edge_verts = np.empty(n_edges * 2, dtype=np.int32)
        mesh.edges.foreach_get("vertices", edge_verts)
        v0 = edge_verts[0::2]
        v1 = edge_verts[1::2]

        # Apply topology constraint — filter edges
        if constraint_mode == "SHARP":
            sharp = np.empty(n_edges, dtype=bool)
            mesh.edges.foreach_get("use_edge_sharp", sharp)
            keep = ~sharp
            v0, v1 = v0[keep], v1[keep]
        elif constraint_mode == "SEAM":
            seam = np.empty(n_edges, dtype=bool)
            mesh.edges.foreach_get("use_seam", seam)
            keep = ~seam
            v0, v1 = v0[keep], v1[keep]
        elif constraint_mode == "BOUNDARY":
            n_loops = len(mesh.loops)
            loop_edges = np.empty(n_loops, dtype=np.int32)
            mesh.loops.foreach_get("edge_index", loop_edges)
            face_count = np.zeros(n_edges, dtype=np.int32)
            np.add.at(face_count, loop_edges, 1)
            keep = face_count > 1
            v0, v1 = v0[keep], v1[keep]

        # Compute per-vertex neighbor counts (constant across iterations)
        neighbor_count = np.zeros(num_verts, dtype=np.float32)
        np.add.at(neighbor_count, v0, 1)
        np.add.at(neighbor_count, v1, 1)
        has_neighbors = neighbor_count > 0

        # Read per-vertex colors from domain
        if color_attribute.domain == "CORNER":
            n_loops = len(mesh.loops)
            loop_verts = np.empty(n_loops, dtype=np.int32)
            mesh.loops.foreach_get("vertex_index", loop_verts)

            # Average loop colors per vertex using add.at
            vert_colors = np.zeros((num_verts, 4), dtype=np.float32)
            loop_count = np.zeros(num_verts, dtype=np.float32)
            np.add.at(vert_colors, loop_verts, all_colors)
            np.add.at(loop_count, loop_verts, 1)
            loop_count = np.maximum(loop_count, 1)
            vert_colors /= loop_count[:, np.newaxis]
        else:
            loop_verts = None
            vert_colors = all_colors.copy()

        # Vectorized iterative smoothing
        for _ in range(iterations):
            neighbor_sum = np.zeros((num_verts, 4), dtype=np.float32)
            np.add.at(neighbor_sum, v0, vert_colors[v1])
            np.add.at(neighbor_sum, v1, vert_colors[v0])

            avg = np.zeros_like(vert_colors)
            avg[has_neighbors] = neighbor_sum[has_neighbors] / neighbor_count[has_neighbors, np.newaxis]

            vert_colors = np.where(
                has_neighbors[:, np.newaxis],
                vert_colors + (avg - vert_colors) * factor,
                vert_colors,
            )

        # Write back with mask
        if color_attribute.domain == "CORNER":
            new_loop_colors = vert_colors[loop_verts]
            apply_mask_array(all_colors, new_loop_colors, mask)
        else:
            apply_mask_array(all_colors, vert_colors, mask)

        bulk_set_colors(color_attribute, all_colors)
        obj.data.update()
