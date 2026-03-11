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
                return self._curvature_values(obj)
            case "WEIGHT":
                return self._weight_values(obj)

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
