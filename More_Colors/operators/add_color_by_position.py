# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from random import Random

import bpy
import numpy as np
from mathutils import Vector
from mathutils.noise import fractal as noise_fractal

from .base_operators import BaseColorOperator, BaseOperator
from ..utilities.color_utilities import (
    apply_mask_array, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute, get_selected_color_indices,
)


class MC_OT_add_color_by_position(BaseColorOperator):
    """Applies a gradient to vertex colors based on the selected source"""

    bl_label = "Apply Gradient"
    bl_idname = "morecolors.add_color_by_position"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool = context.scene.more_colors_color_by_position_tool
        mask = context.scene.more_colors_global_color_settings.get_mask()
        color_ramp = self._get_color_ramp(context)
        select_mode = context.tool_settings.mesh_select_mode if context.mode == 'EDIT_MESH' else None

        any_applied = False
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                values = self._compute_values(obj, tool, context)
                if values is None:
                    continue
                if tool.normalize_per_island:
                    values = self._normalize_per_island(obj, values)
                self._apply_gradient(obj, values, color_ramp, mask, select_mode)
                any_applied = True

        if not any_applied:
            self.report({"ERROR"}, "No active vertex group found on selected objects.")
            return {"CANCELLED"}
        self.report({"INFO"}, "Gradient applied!")
        return {"FINISHED"}

    # ---- Source dispatch ----

    def _compute_values(self, obj, tool, context):
        match tool.gradient_source:
            case "POSITION":
                return self._position_values(obj, tool)
            case "DISTANCE":
                return self._distance_values(obj, tool, context)
            case "NOISE":
                return self._noise_values(obj, tool)
            case "CURVATURE":
                if tool.curvature_use_cotangent:
                    return self._cotangent_curvature_values(obj)
                return self._curvature_values(obj)
            case "WEIGHT":
                return self._weight_values(obj)
            case "DIRTY":
                return self._dirty_values(obj, tool)
            case "VALENCE":
                return self._valence_values(obj)
            case "FACE_AREA":
                return self._face_area_values(obj)
            case "EDGE_LENGTH_VAR":
                return self._edge_length_variance_values(obj)
            case "FACE_QUALITY":
                return self._face_quality_values(obj)

    # ---- Per-source value computation ----

    @staticmethod
    def _get_coords(obj, use_world):
        """Fetch vertex coordinates as (V, 3) numpy array, optionally in world space."""
        n = len(obj.data.vertices)
        coords = np.empty(n * 3, dtype=np.float64)
        obj.data.vertices.foreach_get("co", coords)
        coords = coords.reshape(n, 3)
        if use_world:
            mat = np.array(obj.matrix_world, dtype=np.float64)
            ones = np.ones((n, 1), dtype=np.float64)
            coords = np.hstack([coords, ones]) @ mat.T
            coords = coords[:, :3]
        return coords

    def _position_values(self, obj, tool):
        axis_index = {"X": 0, "Y": 1, "Z": 2}[tool.gradient_direction[-1]]
        reverse = len(tool.gradient_direction) > 1
        use_world = (tool.space_type == "World")

        coords = self._get_coords(obj, use_world)
        values = self._normalize_np(coords[:, axis_index])
        if reverse:
            values = 1.0 - values
        return values

    def _distance_values(self, obj, tool, context):
        match tool.distance_origin:
            case "CURSOR":
                origin_world = context.scene.cursor.location.copy()
            case "OBJECT":
                origin_world = obj.matrix_world.translation.copy()
            case "WORLD":
                origin_world = Vector((0, 0, 0))

        use_world = (tool.space_type == "World")
        origin = origin_world if use_world else obj.matrix_world.inverted() @ origin_world
        origin_np = np.array(origin, dtype=np.float64)

        coords = self._get_coords(obj, use_world)
        distances = np.linalg.norm(coords - origin_np, axis=1)
        return self._normalize_np(distances)

    def _noise_values(self, obj, tool):
        rng = Random(tool.noise_seed)
        offset = Vector((
            rng.uniform(-1000, 1000),
            rng.uniform(-1000, 1000),
            rng.uniform(-1000, 1000),
        ))
        scale = tool.noise_scale
        octaves = tool.noise_detail + 1
        use_world = (tool.space_type == "World")

        coords = self._get_coords(obj, use_world)
        n = len(coords)
        raw = np.empty(n, dtype=np.float64)
        for i in range(n):
            raw[i] = noise_fractal(Vector(coords[i]) * scale + offset, 1.0, 2.0, octaves)
        return self._normalize_np(raw)

    @staticmethod
    def _curvature_values(obj):
        mesh = obj.data
        n = len(mesh.vertices)

        coords = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("co", coords)
        coords = coords.reshape(n, 3)

        normals = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("normal", normals)
        normals = normals.reshape(n, 3)

        # Vectorized neighbor accumulation via edge data
        n_edges = len(mesh.edges)
        edge_verts = np.empty(n_edges * 2, dtype=np.int32)
        mesh.edges.foreach_get("vertices", edge_verts)
        v0 = edge_verts[0::2]
        v1 = edge_verts[1::2]

        neighbor_sum = np.zeros((n, 3), dtype=np.float64)
        neighbor_count = np.zeros(n, dtype=np.float64)
        np.add.at(neighbor_sum, v0, coords[v1])
        np.add.at(neighbor_sum, v1, coords[v0])
        np.add.at(neighbor_count, v0, 1)
        np.add.at(neighbor_count, v1, 1)

        has_neighbors = neighbor_count > 0
        avg = np.zeros_like(coords)
        avg[has_neighbors] = neighbor_sum[has_neighbors] / neighbor_count[has_neighbors, np.newaxis]

        # Laplacian dot normal: positive = concave, negative = convex
        raw = np.sum((avg - coords) * normals, axis=1)
        raw[~has_neighbors] = 0.0
        return MC_OT_add_color_by_position._normalize_np(raw)

    @staticmethod
    def _weight_values(obj):
        group = obj.vertex_groups.active
        if group is None:
            return None
        n = len(obj.data.vertices)
        values = np.zeros(n, dtype=np.float64)
        for v in obj.data.vertices:
            try:
                values[v.index] = group.weight(v.index)
            except RuntimeError:
                pass
        return values

    @staticmethod
    def _dirty_values(obj, tool):
        """Compute per-vertex dirt (cavity/occlusion) values.

        Matches Blender's native Dirty Vertex Colors algorithm:
        for each vertex, average the directions to all connected
        neighbours, then measure the angle between that average
        direction and the vertex normal.
          angle < 90 °  →  concave (dirt)   →  low tone (dark)
          angle > 90 °  →  convex  (clean)  →  high tone (bright)
          angle ≈ 90 °  →  flat             →  mid tone
        """
        mesh = obj.data
        n = len(mesh.vertices)

        coords = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("co", coords)
        coords = coords.reshape(n, 3)

        normals = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("normal", normals)
        normals = normals.reshape(n, 3)

        # Edge pair arrays
        n_edges = len(mesh.edges)
        edge_verts = np.empty(n_edges * 2, dtype=np.int32)
        mesh.edges.foreach_get("vertices", edge_verts)
        v0 = edge_verts[0::2]
        v1 = edge_verts[1::2]

        # For each edge, compute the normalized direction to the neighbour
        d01 = coords[v1] - coords[v0]
        d10 = -d01
        len01 = np.linalg.norm(d01, axis=1, keepdims=True)
        len01 = np.maximum(len01, 1e-12)
        d01 /= len01
        d10 /= len01

        # Accumulate average neighbour direction per vertex
        dir_sum = np.zeros((n, 3), dtype=np.float64)
        dir_count = np.zeros(n, dtype=np.float64)
        np.add.at(dir_sum, v0, d01)
        np.add.at(dir_sum, v1, d10)
        np.add.at(dir_count, v0, 1)
        np.add.at(dir_count, v1, 1)

        has_neighbors = dir_count > 0
        dir_sum[has_neighbors] /= dir_count[has_neighbors, np.newaxis]

        # angle = acos(normal · avg_dir), clamped to [-1, 1]
        dot = np.sum(normals * dir_sum, axis=1)
        dot = np.clip(dot, -1.0, 1.0)
        angles = np.where(has_neighbors, np.arccos(dot), np.pi / 2.0)

        # Clamp with dirt/highlight angle thresholds
        angles = np.maximum(angles, tool.dirt_dirt_angle)
        if not tool.dirt_only_dirty:
            angles = np.minimum(angles, tool.dirt_highlight_angle)

        # Blur passes (operate on angle values, matching Blender)
        strength = tool.dirt_blur_strength
        for _ in range(tool.dirt_blur_iterations):
            orig = angles.copy()
            neighbor_sum = np.zeros(n, dtype=np.float64)
            np.add.at(neighbor_sum, v0, orig[v1])
            np.add.at(neighbor_sum, v1, orig[v0])
            blurred = np.where(
                has_neighbors,
                (angles + neighbor_sum * strength) / (dir_count * strength + 1.0),
                angles,
            )
            angles = blurred

        # Normalize to 0-1
        if tool.dirt_normalize:
            min_tone = angles.min()
            max_tone = angles.max()
        else:
            min_tone = tool.dirt_dirt_angle
            max_tone = tool.dirt_highlight_angle

        tone_range = max_tone - min_tone
        if tone_range < 1e-4:
            values = np.zeros(n, dtype=np.float64)
        else:
            values = (angles - min_tone) / tone_range

        if tool.dirt_only_dirty:
            values = np.minimum(values, 0.5) * 2.0

        return values

    @staticmethod
    def _valence_values(obj):
        """Per-vertex edge valence (number of connected edges)."""
        mesh = obj.data
        n = len(mesh.vertices)
        n_edges = len(mesh.edges)
        edge_verts = np.empty(n_edges * 2, dtype=np.int32)
        mesh.edges.foreach_get("vertices", edge_verts)
        v0 = edge_verts[0::2]
        v1 = edge_verts[1::2]

        valence = np.zeros(n, dtype=np.float64)
        np.add.at(valence, v0, 1)
        np.add.at(valence, v1, 1)
        return MC_OT_add_color_by_position._normalize_np(valence)

    @staticmethod
    def _face_area_values(obj):
        """Average area of adjacent faces per vertex."""
        mesh = obj.data
        n = len(mesh.vertices)
        n_polys = len(mesh.polygons)
        n_loops = len(mesh.loops)

        areas = np.empty(n_polys, dtype=np.float64)
        mesh.polygons.foreach_get("area", areas)

        loop_verts = np.empty(n_loops, dtype=np.int32)
        mesh.loops.foreach_get("vertex_index", loop_verts)

        loop_totals = np.empty(n_polys, dtype=np.int32)
        mesh.polygons.foreach_get("loop_total", loop_totals)

        # Map each loop to its face index
        loop_face = np.repeat(np.arange(n_polys, dtype=np.int32), loop_totals)

        area_sum = np.zeros(n, dtype=np.float64)
        area_count = np.zeros(n, dtype=np.float64)
        np.add.at(area_sum, loop_verts, areas[loop_face])
        np.add.at(area_count, loop_verts, 1)
        area_count = np.maximum(area_count, 1)

        return MC_OT_add_color_by_position._normalize_np(area_sum / area_count)

    @staticmethod
    def _edge_length_variance_values(obj):
        """Variance of connected edge lengths per vertex."""
        mesh = obj.data
        n = len(mesh.vertices)

        coords = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("co", coords)
        coords = coords.reshape(n, 3)

        n_edges = len(mesh.edges)
        edge_verts = np.empty(n_edges * 2, dtype=np.int32)
        mesh.edges.foreach_get("vertices", edge_verts)
        v0 = edge_verts[0::2]
        v1 = edge_verts[1::2]

        edge_lengths = np.linalg.norm(coords[v1] - coords[v0], axis=1)

        edge_sum = np.zeros(n, dtype=np.float64)
        edge_sq_sum = np.zeros(n, dtype=np.float64)
        edge_count = np.zeros(n, dtype=np.float64)
        np.add.at(edge_sum, v0, edge_lengths)
        np.add.at(edge_sum, v1, edge_lengths)
        np.add.at(edge_sq_sum, v0, edge_lengths ** 2)
        np.add.at(edge_sq_sum, v1, edge_lengths ** 2)
        np.add.at(edge_count, v0, 1)
        np.add.at(edge_count, v1, 1)

        has_edges = edge_count > 0
        mean_len = np.zeros(n, dtype=np.float64)
        mean_len[has_edges] = edge_sum[has_edges] / edge_count[has_edges]

        variance = np.zeros(n, dtype=np.float64)
        variance[has_edges] = (
            edge_sq_sum[has_edges] / edge_count[has_edges]
            - mean_len[has_edges] ** 2
        )
        return MC_OT_add_color_by_position._normalize_np(variance)

    @staticmethod
    def _face_quality_values(obj):
        """Regularity of adjacent faces per vertex.

        Uses the isoperimetric quotient normalised per polygon side count so
        that any regular polygon scores 1.0 and degenerate faces approach 0.
        """
        mesh = obj.data
        n = len(mesh.vertices)
        n_polys = len(mesh.polygons)
        n_loops = len(mesh.loops)

        coords = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("co", coords)
        coords = coords.reshape(n, 3)

        areas = np.empty(n_polys, dtype=np.float64)
        mesh.polygons.foreach_get("area", areas)

        loop_verts = np.empty(n_loops, dtype=np.int32)
        mesh.loops.foreach_get("vertex_index", loop_verts)

        loop_starts = np.empty(n_polys, dtype=np.int32)
        loop_totals = np.empty(n_polys, dtype=np.int32)
        mesh.polygons.foreach_get("loop_start", loop_starts)
        mesh.polygons.foreach_get("loop_total", loop_totals)

        # Build "next vertex in face" for each loop — fully vectorized
        next_loop = np.arange(1, n_loops + 1, dtype=np.int32)
        face_ends = loop_starts + loop_totals - 1
        next_loop[face_ends] = loop_starts

        # Per-loop edge lengths
        edge_vectors = coords[loop_verts[next_loop]] - coords[loop_verts]
        edge_lengths = np.linalg.norm(edge_vectors, axis=1)

        # Map each loop to its face index
        loop_face = np.repeat(np.arange(n_polys, dtype=np.int32), loop_totals)

        # Per-face perimeter
        perimeter = np.zeros(n_polys, dtype=np.float64)
        np.add.at(perimeter, loop_face, edge_lengths)

        # Isoperimetric quotient: 4*pi*area / perimeter^2
        quality = np.zeros(n_polys, dtype=np.float64)
        safe = perimeter > 1e-12
        quality[safe] = 4.0 * np.pi * areas[safe] / (perimeter[safe] ** 2)

        # Normalise per polygon type so regular n-gons score 1.0
        safe_totals = np.maximum(loop_totals, 3).astype(np.float64)
        regular_factor = safe_totals * np.tan(np.pi / safe_totals) / np.pi
        quality *= regular_factor

        # Average quality per vertex
        quality_per_loop = quality[loop_face]
        quality_sum = np.zeros(n, dtype=np.float64)
        quality_count = np.zeros(n, dtype=np.float64)
        np.add.at(quality_sum, loop_verts, quality_per_loop)
        np.add.at(quality_count, loop_verts, 1)
        quality_count = np.maximum(quality_count, 1)

        return MC_OT_add_color_by_position._normalize_np(quality_sum / quality_count)

    @staticmethod
    def _cotangent_curvature_values(obj):
        """Mean curvature via cotangent-weighted Laplacian.

        For each edge, uses the cotangent of the two opposite angles in
        the adjacent triangles as weights.  Produces smoother results than
        the simple uniform-weight Laplacian in ``_curvature_values``,
        especially on irregular meshes.  Non-manifold edges (boundary or
        more than 2 adjacent faces) fall back to uniform weight = 1.
        """
        mesh = obj.data
        n = len(mesh.vertices)
        n_edges = len(mesh.edges)
        n_polys = len(mesh.polygons)
        n_loops = len(mesh.loops)

        # Vertex positions & normals
        coords = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("co", coords)
        coords = coords.reshape(n, 3)

        normals = np.empty(n * 3, dtype=np.float64)
        mesh.vertices.foreach_get("normal", normals)
        normals = normals.reshape(n, 3)

        # Edge vertex pairs
        edge_verts = np.empty(n_edges * 2, dtype=np.int32)
        mesh.edges.foreach_get("vertices", edge_verts)
        v0 = edge_verts[0::2]
        v1 = edge_verts[1::2]

        # Loop data for building edge→opposite-vertex map
        loop_verts = np.empty(n_loops, dtype=np.int32)
        mesh.loops.foreach_get("vertex_index", loop_verts)
        loop_edge_idx = np.empty(n_loops, dtype=np.int32)
        mesh.loops.foreach_get("edge_index", loop_edge_idx)
        loop_starts = np.empty(n_polys, dtype=np.int32)
        loop_totals = np.empty(n_polys, dtype=np.int32)
        mesh.polygons.foreach_get("loop_start", loop_starts)
        mesh.polygons.foreach_get("loop_total", loop_totals)

        # Build "next loop in face" index array (wrapping)
        next_loop = np.arange(1, n_loops + 1, dtype=np.int32)
        face_ends = loop_starts + loop_totals - 1
        next_loop[face_ends] = loop_starts

        # For each loop, its "previous" loop in the same face
        prev_loop = np.empty(n_loops, dtype=np.int32)
        prev_loop[next_loop[np.arange(n_loops)]] = np.arange(n_loops, dtype=np.int32)

        # For each loop that belongs to an edge, compute the cotangent
        # of the angle at the *opposite* vertex in that triangle.
        # The opposite vertex is the vertex of the face that is NOT on the edge.
        # In a polygon with >3 sides, we use the two vertices adjacent to
        # the edge vertices within the face (next of v1 loop, prev of v0 loop).
        # For triangles this gives the single opposite vertex.

        # Accumulate cotangent weights per edge from each adjacent face.
        cot_weight = np.zeros(n_edges, dtype=np.float64)
        cot_count = np.zeros(n_edges, dtype=np.int32)

        # Map loops to faces
        loop_face = np.repeat(np.arange(n_polys, dtype=np.int32), loop_totals)

        # For each loop, get the edge it belongs to and the opposite tip vertex.
        # The "opposite" for a loop with edge (A,B) is the vertex at the tip
        # of the triangle containing that edge.  For a triangle face, this is
        # the remaining vertex.  We find it as: for the loop whose edge goes
        # A→B, the next vertex in the face after B is the opposite tip
        # (for a triangle, this is correct; for n-gons it's a reasonable
        # approximation).

        # For each loop i, edge_index tells us which edge it contains.
        # The opposite vertex is at the position *two loops ahead* for
        # a triangle.  For general polygons we use the vertex that is
        # neither endpoint of the edge.

        # Approach: iterate faces in Python (fast enough — one pass over faces)
        # to find per-edge opposite vertices, then vectorize the cotangent.

        # Build per-edge list of opposite vertex indices
        # (up to 2 per edge for manifold meshes)
        opp_edge = []
        opp_vert = []
        ls = loop_starts
        lt = loop_totals
        for fi in range(n_polys):
            start = ls[fi]
            total = lt[fi]
            if total < 3:
                continue
            face_loop_verts = loop_verts[start:start + total]
            face_loop_edges = loop_edge_idx[start:start + total]
            for li in range(total):
                ei = face_loop_edges[li]
                # The edge connects face_loop_verts[li] → face_loop_verts[(li+1)%total].
                # The opposite vertex for this edge in this face is face_loop_verts[(li+2)%total]
                # (works exactly for tris; for quads+ it's the first non-edge vertex).
                opp_idx = (li + 2) % total
                opp_edge.append(ei)
                opp_vert.append(face_loop_verts[opp_idx])

        if opp_edge:
            opp_edge = np.array(opp_edge, dtype=np.int32)
            opp_vert_arr = np.array(opp_vert, dtype=np.int32)

            # Cotangent of the angle at opp_vert for the triangle formed by
            # edge endpoints and the opposite vertex.
            ev0 = v0[opp_edge]
            ev1 = v1[opp_edge]
            a_vec = coords[ev0] - coords[opp_vert_arr]
            b_vec = coords[ev1] - coords[opp_vert_arr]
            dot = np.sum(a_vec * b_vec, axis=1)
            cross_mag = np.linalg.norm(np.cross(a_vec, b_vec), axis=1)
            cross_mag = np.maximum(cross_mag, 1e-12)
            cot = dot / cross_mag

            np.add.at(cot_weight, opp_edge, cot)
            np.add.at(cot_count, opp_edge, 1)

        # Edges with no adjacent faces get uniform weight
        no_adj = cot_count == 0
        cot_weight[no_adj] = 1.0

        # Clamp to avoid negative weights from obtuse angles
        cot_weight = np.maximum(cot_weight, 1e-6)

        # Weighted Laplacian: sum_j w_ij * (p_j - p_i)
        diff_01 = coords[v1] - coords[v0]  # v0 toward v1
        diff_10 = -diff_01                   # v1 toward v0

        weighted_lap = np.zeros((n, 3), dtype=np.float64)
        weight_sum = np.zeros(n, dtype=np.float64)
        np.add.at(weighted_lap, v0, cot_weight[:, np.newaxis] * diff_01)
        np.add.at(weighted_lap, v1, cot_weight[:, np.newaxis] * diff_10)
        np.add.at(weight_sum, v0, cot_weight)
        np.add.at(weight_sum, v1, cot_weight)

        has_neighbors = weight_sum > 0
        weighted_lap[has_neighbors] /= weight_sum[has_neighbors, np.newaxis]

        # Mean curvature ~ Laplacian dot normal
        raw = np.sum(weighted_lap * normals, axis=1)
        raw[~has_neighbors] = 0.0
        return MC_OT_add_color_by_position._normalize_np(raw)

    # ---- Shared helpers ----

    @staticmethod
    def _normalize_np(values):
        """Normalize values to 0–1 range via min-max scaling."""
        if len(values) == 0:
            return values
        min_val = values.min()
        max_val = values.max()
        val_range = max_val - min_val
        if val_range == 0:
            return np.zeros_like(values)
        return (values - min_val) / val_range

    @staticmethod
    def _normalize_per_island(obj, values):
        """Re-normalize values independently per connected mesh island."""
        mesh = obj.data
        n_polys = len(mesh.polygons)
        if n_polys == 0:
            return values

        # Build edge -> face adjacency
        edge_to_faces = {}
        for poly_index in range(n_polys):
            poly = mesh.polygons[poly_index]
            for edge_key in poly.edge_keys:
                edge_to_faces.setdefault(edge_key, []).append(poly_index)

        adjacency = [[] for _ in range(n_polys)]
        for face_list in edge_to_faces.values():
            for i in range(len(face_list)):
                for j in range(i + 1, len(face_list)):
                    adjacency[face_list[i]].append(face_list[j])
                    adjacency[face_list[j]].append(face_list[i])

        # Flood-fill connected components and normalize each
        visited = np.zeros(n_polys, dtype=bool)
        result = values.copy()

        for start in range(n_polys):
            if visited[start]:
                continue
            queue = [start]
            visited[start] = True
            island_faces = []
            while queue:
                face = queue.pop()
                island_faces.append(face)
                for neighbor in adjacency[face]:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)

            island_verts = set()
            for fi in island_faces:
                island_verts.update(mesh.polygons[fi].vertices)
            idx = np.array(sorted(island_verts), dtype=np.intp)

            island_vals = result[idx]
            min_val = island_vals.min()
            val_range = island_vals.max() - min_val
            if val_range > 0:
                result[idx] = (island_vals - min_val) / val_range
            else:
                result[idx] = 0.0

        return result

    @staticmethod
    def _apply_gradient(obj, values, color_ramp, mask, select_mode):
        color_attribute = get_active_color_attribute(obj)
        indices = get_selected_color_indices(obj, select_mode, color_attribute.domain)
        colors = bulk_get_colors(color_attribute)

        if color_attribute.domain == "CORNER":
            n_loops = len(obj.data.loops)
            loop_verts = np.empty(n_loops, dtype=np.int32)
            obj.data.loops.foreach_get("vertex_index", loop_verts)

            target_loops = np.arange(n_loops, dtype=np.intp) if indices is None else indices

            # Evaluate color ramp only for unique vertices used by target loops
            unique_verts, inverse = np.unique(loop_verts[target_loops], return_inverse=True)
            ramp_colors = np.array(
                [color_ramp.evaluate(float(values[vi])) for vi in unique_verts],
                dtype=np.float32,
            )
            new_colors = ramp_colors[inverse]
            apply_mask_array(colors, new_colors, mask, target_loops)

        elif color_attribute.domain == "POINT":
            n_verts = len(obj.data.vertices)
            target_verts = np.arange(n_verts, dtype=np.intp) if indices is None else indices
            new_colors = np.array(
                [color_ramp.evaluate(float(values[vi])) for vi in target_verts],
                dtype=np.float32,
            )
            apply_mask_array(colors, new_colors, mask, target_verts)

        bulk_set_colors(color_attribute, colors)
        obj.data.update()

    def _get_color_ramp(self, context):
        tool = context.scene.more_colors_color_by_position_tool
        material_name = tool.color_ramp_material_name
        material = bpy.data.materials.get(material_name)
        if material is None:
            material = bpy.data.materials.new(name=material_name)
            material.use_nodes = True
            nodes = material.node_tree.nodes
            nodes.clear()
            nodes.new(type="ShaderNodeValToRGB")
        node = material.node_tree.nodes["Color Ramp"]
        return node.color_ramp


class MC_OT_reset_color_by_position_gradient(BaseOperator):
    """Resets the gradient to a default black and white value"""

    bl_label = "Reset Gradient"
    bl_idname = "morecolors.reset_color_by_position_gradient"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        color_by_position_tool = context.scene.more_colors_color_by_position_tool
        material_name = color_by_position_tool.color_ramp_material_name

        material = bpy.data.materials.get(material_name)
        if material is None:
            self.report({"ERROR"}, "No gradient to reset.")
            return {"CANCELLED"}

        node = material.node_tree.nodes["Color Ramp"]
        color_ramp = node.color_ramp

        # Color Ramp node needs at least one element, so we don't delete the first one
        while len(color_ramp.elements) > 1:
            color_ramp.elements.remove(color_ramp.elements[0])

        black = node.color_ramp.elements[0]
        black.position = 0
        black.color = (0, 0, 0, 1)

        white = node.color_ramp.elements.new(1)
        white.color = (1, 1, 1, 1)

        return {"FINISHED"}
