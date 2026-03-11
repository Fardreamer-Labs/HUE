# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from random import Random

import bpy
from mathutils import Vector
from mathutils.noise import fractal as noise_fractal

from .base_operators import BaseColorOperator, BaseOperator
from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode, get_masked_color, get_active_color_attribute
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

        any_applied = False
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                values = self._compute_values(obj, tool, context)
                if values is None:
                    continue
                self._apply_gradient(obj, values, color_ramp, mask)
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

    def _position_values(self, obj, tool):
        axis_index = {"X": 0, "Y": 1, "Z": 2}[tool.gradient_direction[-1]]
        reverse = len(tool.gradient_direction) > 1
        use_world = (tool.space_type == "World")

        raw = [
            (obj.matrix_world @ v.co if use_world else v.co)[axis_index]
            for v in obj.data.vertices
        ]
        values = self._normalize(raw)
        if reverse:
            values = [1.0 - v for v in values]
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

        raw = [
            ((obj.matrix_world @ v.co if use_world else v.co) - origin).length
            for v in obj.data.vertices
        ]
        return self._normalize(raw)

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

        raw = [
            noise_fractal(
                (obj.matrix_world @ v.co if use_world else v.co) * scale + offset,
                1.0, 2.0, octaves
            )
            for v in obj.data.vertices
        ]
        return self._normalize(raw)

    @staticmethod
    def _curvature_values(obj):
        mesh = obj.data
        num_verts = len(mesh.vertices)

        # Build adjacency: vertex -> neighbor vertex indices
        neighbors = [[] for _ in range(num_verts)]
        for edge in mesh.edges:
            v0, v1 = edge.vertices
            neighbors[v0].append(v1)
            neighbors[v1].append(v0)

        raw = []
        for v in mesh.vertices:
            if not neighbors[v.index]:
                raw.append(0.0)
                continue
            avg = Vector((0, 0, 0))
            for ni in neighbors[v.index]:
                avg += mesh.vertices[ni].co
            avg /= len(neighbors[v.index])
            # Laplacian dot normal: positive = concave, negative = convex
            raw.append((avg - v.co).dot(v.normal))

        return MC_OT_add_color_by_position._normalize(raw)

    @staticmethod
    def _weight_values(obj):
        group = obj.vertex_groups.active
        if group is None:
            return None
        values = []
        for v in obj.data.vertices:
            try:
                values.append(group.weight(v.index))
            except RuntimeError:
                values.append(0.0)
        return values

    # ---- Shared helpers ----

    @staticmethod
    def _normalize(raw):
        """Normalize values to 0–1 range via min-max scaling."""
        if not raw:
            return []
        min_val = min(raw)
        max_val = max(raw)
        val_range = max_val - min_val
        if val_range == 0:
            return [0.0] * len(raw)
        return [(v - min_val) / val_range for v in raw]

    @staticmethod
    def _apply_gradient(obj, values, color_ramp, mask):
        color_attribute = get_active_color_attribute(obj)
        match color_attribute.domain:
            case "CORNER":
                vert_to_loops = build_vertex_loop_map(obj)
                for vert in obj.data.vertices:
                    color = color_ramp.evaluate(values[vert.index])
                    for loop_index in vert_to_loops.get(vert.index, []):
                        data = color_attribute.data[loop_index]
                        data.color_srgb = get_masked_color(data.color_srgb, color, mask)
            case "POINT":
                for vert in obj.data.vertices:
                    color = color_ramp.evaluate(values[vert.index])
                    data = color_attribute.data[vert.index]
                    data.color_srgb = get_masked_color(data.color_srgb, color, mask)
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
