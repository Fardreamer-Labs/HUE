# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

from .base_operators import BaseColorOperator
from ..utilities.color_utilities import (
    apply_mask_array, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute, get_selected_color_indices,
)


class MC_OT_attribute_transfer(BaseColorOperator):
    """Transfers vertex colors from a source object to the active object"""

    bl_label = "Transfer Colors"
    bl_idname = "morecolors.attribute_transfer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool = context.scene.more_colors_attribute_transfer_tool
        mask = context.scene.more_colors_global_color_settings.get_mask()
        select_mode = context.tool_settings.mesh_select_mode if context.mode == 'EDIT_MESH' else None

        source = tool.source_object
        if source is None:
            self.report({"ERROR"}, "No source object selected.")
            return {"CANCELLED"}
        if source.type != "MESH":
            self.report({"ERROR"}, "Source object must be a mesh.")
            return {"CANCELLED"}

        for obj in context.selected_objects:
            if obj.type != "MESH" or obj is source:
                continue
            with ensure_object_mode(obj):
                self._transfer(obj, source, tool, mask, select_mode)

        self.report({"INFO"}, "Colors transferred!")
        return {"FINISHED"}

    @staticmethod
    def _transfer(obj, source, tool, mask, select_mode):
        # -- Source color data (read in world space) --
        src_attr = (
            source.data.color_attributes.get(tool.source_layer)
            if tool.source_layer
            else get_active_color_attribute(source)
        )
        if src_attr is None:
            src_attr = get_active_color_attribute(source)
        src_colors = bulk_get_colors(src_attr)

        n_src = len(source.data.vertices)
        src_coords = np.empty(n_src * 3, dtype=np.float64)
        source.data.vertices.foreach_get("co", src_coords)
        src_coords = src_coords.reshape(n_src, 3)
        src_mat = np.array(source.matrix_world, dtype=np.float64)

        # Source vertex world positions
        ones_src = np.ones((n_src, 1), dtype=np.float64)
        src_world = np.hstack([src_coords, ones_src]) @ src_mat.T
        src_world = src_world[:, :3]

        # Per-vertex colors on source (average loops if CORNER domain)
        if src_attr.domain == "CORNER":
            n_loops = len(source.data.loops)
            src_loop_verts = np.empty(n_loops, dtype=np.int32)
            source.data.loops.foreach_get("vertex_index", src_loop_verts)
            src_vert_colors = np.zeros((n_src, 4), dtype=np.float32)
            src_vert_counts = np.zeros(n_src, dtype=np.float32)
            np.add.at(src_vert_colors, src_loop_verts, src_colors)
            np.add.at(src_vert_counts, src_loop_verts, 1)
            src_vert_counts = np.maximum(src_vert_counts, 1)
            src_vert_colors /= src_vert_counts[:, np.newaxis]
        else:
            src_vert_colors = src_colors

        # -- Target setup --
        color_attribute = get_active_color_attribute(obj)
        indices = get_selected_color_indices(obj, select_mode, color_attribute.domain)
        colors = bulk_get_colors(color_attribute)

        n_tgt = len(obj.data.vertices)
        tgt_coords = np.empty(n_tgt * 3, dtype=np.float64)
        obj.data.vertices.foreach_get("co", tgt_coords)
        tgt_coords = tgt_coords.reshape(n_tgt, 3)
        tgt_mat = np.array(obj.matrix_world, dtype=np.float64)

        ones_tgt = np.ones((n_tgt, 1), dtype=np.float64)
        tgt_world = np.hstack([tgt_coords, ones_tgt]) @ tgt_mat.T
        tgt_world = tgt_world[:, :3]

        # Per-vertex transferred color
        match tool.transfer_mode:
            case "NEAREST_VERTEX":
                transferred = _nearest_vertex_transfer(
                    tgt_world, src_world, src_vert_colors,
                )
            case "NEAREST_SURFACE":
                transferred = _nearest_surface_transfer(
                    tgt_world, source, src_attr, src_colors,
                )
            case "RAYCAST":
                tgt_normals = np.empty(n_tgt * 3, dtype=np.float64)
                obj.data.vertices.foreach_get("normal", tgt_normals)
                tgt_normals = tgt_normals.reshape(n_tgt, 3)
                # Transform normals to world space (rotation only)
                tgt_norm_mat = np.array(obj.matrix_world.to_3x3().normalized(), dtype=np.float64)
                tgt_normals_world = tgt_normals @ tgt_norm_mat.T
                transferred = _raycast_transfer(
                    tgt_world, tgt_normals_world, source, src_attr, src_colors,
                )

        # Apply mix factor
        if tool.mix_factor < 1.0:
            # Build existing per-vertex colors for blending
            if color_attribute.domain == "CORNER":
                n_loops_tgt = len(obj.data.loops)
                tgt_loop_verts = np.empty(n_loops_tgt, dtype=np.int32)
                obj.data.loops.foreach_get("vertex_index", tgt_loop_verts)
                existing = np.zeros((n_tgt, 4), dtype=np.float32)
                existing_count = np.zeros(n_tgt, dtype=np.float32)
                np.add.at(existing, tgt_loop_verts, colors)
                np.add.at(existing_count, tgt_loop_verts, 1)
                existing_count = np.maximum(existing_count, 1)
                existing /= existing_count[:, np.newaxis]
            else:
                existing = colors.copy()
            transferred = existing + (transferred - existing) * tool.mix_factor

        # Map per-vertex colors to target domain
        target = np.arange(len(colors), dtype=np.intp) if indices is None else indices
        if color_attribute.domain == "CORNER":
            n_loops_tgt = len(obj.data.loops)
            tgt_loop_verts = np.empty(n_loops_tgt, dtype=np.int32)
            obj.data.loops.foreach_get("vertex_index", tgt_loop_verts)
            new_colors = transferred[tgt_loop_verts[target]]
        else:
            new_colors = transferred[target]

        apply_mask_array(colors, new_colors, mask, target)
        bulk_set_colors(color_attribute, colors)
        obj.data.update()


# ---------------------------------------------------------------------------
# Transfer strategies
# ---------------------------------------------------------------------------

def _nearest_vertex_transfer(tgt_world, src_world, src_vert_colors):
    """Transfer colors from the nearest source vertex using a KDTree."""
    n_src = len(src_world)
    tree = KDTree(n_src)
    for i in range(n_src):
        tree.insert(Vector(src_world[i]), i)
    tree.balance()

    n_tgt = len(tgt_world)
    result = np.empty((n_tgt, 4), dtype=np.float32)
    for i in range(n_tgt):
        _, idx, _ = tree.find(Vector(tgt_world[i]))
        result[i] = src_vert_colors[idx]
    return result


def _nearest_surface_transfer(tgt_world, source, src_attr, src_colors):
    """Transfer colors from the nearest point on the source surface."""
    n_tgt = len(tgt_world)
    result = np.empty((n_tgt, 4), dtype=np.float32)
    inv_mat = source.matrix_world.inverted()

    for i in range(n_tgt):
        world_pt = Vector(tgt_world[i])
        local_pt = inv_mat @ world_pt
        success, location, normal, face_index = source.closest_point_on_mesh(local_pt)
        if success and face_index >= 0:
            result[i] = _sample_face_color(source, src_attr, src_colors, face_index, location)
        else:
            result[i] = (0.0, 0.0, 0.0, 1.0)
    return result


def _raycast_transfer(tgt_world, tgt_normals_world, source, src_attr, src_colors):
    """Transfer colors by raycasting from target vertices along their normals."""
    n_tgt = len(tgt_world)
    result = np.empty((n_tgt, 4), dtype=np.float32)
    inv_mat = source.matrix_world.inverted()

    for i in range(n_tgt):
        world_pt = Vector(tgt_world[i])
        world_dir = Vector(tgt_normals_world[i])
        local_pt = inv_mat @ world_pt
        local_dir = (inv_mat.to_3x3() @ world_dir).normalized()

        # Try both directions along the normal
        hit = False
        for direction in (local_dir, -local_dir):
            success, location, normal, face_index = source.ray_cast(local_pt, direction)
            if success and face_index >= 0:
                result[i] = _sample_face_color(source, src_attr, src_colors, face_index, location)
                hit = True
                break
        if not hit:
            # Fall back to nearest surface
            success, location, normal, face_index = source.closest_point_on_mesh(local_pt)
            if success and face_index >= 0:
                result[i] = _sample_face_color(source, src_attr, src_colors, face_index, location)
            else:
                result[i] = (0.0, 0.0, 0.0, 1.0)
    return result


def _sample_face_color(source, src_attr, src_colors, face_index, location):
    """Sample interpolated color at *location* on *face_index* using barycentric coords."""
    poly = source.data.polygons[face_index]
    loop_start = poly.loop_start
    verts = [source.data.loops[loop_start + j].vertex_index for j in range(poly.loop_total)]

    if len(verts) < 3:
        if src_attr.domain == "CORNER":
            return src_colors[loop_start]
        return src_colors[verts[0]] if verts else np.array([0, 0, 0, 1], dtype=np.float32)

    # Use first three vertices for barycentric interpolation
    co = [Vector(source.data.vertices[vi].co) for vi in verts[:3]]
    loc = Vector(location)

    # Barycentric weights
    v0 = co[1] - co[0]
    v1 = co[2] - co[0]
    v2 = loc - co[0]
    d00 = v0.dot(v0)
    d01 = v0.dot(v1)
    d11 = v1.dot(v1)
    d20 = v2.dot(v0)
    d21 = v2.dot(v1)
    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-12:
        # Degenerate face — use first vertex color
        if src_attr.domain == "CORNER":
            return src_colors[loop_start]
        return src_colors[verts[0]]

    bary_v = (d11 * d20 - d01 * d21) / denom
    bary_w = (d00 * d21 - d01 * d20) / denom
    bary_u = 1.0 - bary_v - bary_w

    if src_attr.domain == "CORNER":
        c0 = src_colors[loop_start]
        c1 = src_colors[loop_start + 1]
        c2 = src_colors[loop_start + 2]
    else:
        c0 = src_colors[verts[0]]
        c1 = src_colors[verts[1]]
        c2 = src_colors[verts[2]]

    return c0 * bary_u + c1 * bary_v + c2 * bary_w
