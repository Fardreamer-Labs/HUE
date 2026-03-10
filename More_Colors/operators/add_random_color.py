# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode,
    get_masked_color, get_random_color, get_active_color_attribute, get_distinct_random_colors
)
from .base_operators import BaseColorOperator


class MC_OT_add_random_color(BaseColorOperator):
    """Adds a random color per chosen element (point, vertex, face) for each selected mesh object"""

    bl_label = "Add Random Color"
    bl_idname = "morecolors.add_random_color"
    bl_options = {'REGISTER', 'UNDO'}

    def add_random_color_per_face(self, obj, color_attribute, global_color_settings, random_color_tool, palette):
        mask = global_color_settings.get_mask()
        for poly in obj.data.polygons:
            random_color = get_random_color(random_color_tool.color_mode, palette=palette)
            for loop_index in poly.loop_indices:
                data = color_attribute.data[loop_index]
                data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_point(self, obj, color_attribute, global_color_settings, random_color_tool, palette):
        vert_to_loops = build_vertex_loop_map(obj)
        mask = global_color_settings.get_mask()
        for vert in obj.data.vertices:
            random_color = get_random_color(random_color_tool.color_mode, palette=palette)
            for loop_index in vert_to_loops.get(vert.index, []):
                data = color_attribute.data[loop_index]
                data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_vertex(self, color_attribute, global_color_settings, random_color_tool, palette):
        mask = global_color_settings.get_mask()
        for data in color_attribute.data:
            random_color = get_random_color(random_color_tool.color_mode, palette=palette)
            data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_island(self, obj, color_attribute, global_color_settings, random_color_tool, palette):
        def get_connected_faces(face_index, visited_faces, adjacency_list):
            connected_faces = {face_index}
            faces_to_check = [face_index]

            while faces_to_check:
                current_face = faces_to_check.pop()
                for neighbor in adjacency_list[current_face]:
                    if neighbor not in visited_faces:
                        visited_faces.add(neighbor)
                        connected_faces.add(neighbor)
                        faces_to_check.append(neighbor)

            return connected_faces

        # Build edge_key -> face list in a single pass over polygons
        edge_to_faces = {}
        for poly_index, poly in enumerate(obj.data.polygons):
            for edge_key in poly.edge_keys:
                edge_to_faces.setdefault(edge_key, []).append(poly_index)

        # Build adjacency from edge_to_faces
        adjacency_list = {i: [] for i in range(len(obj.data.polygons))}
        for face_list in edge_to_faces.values():
            for i in range(len(face_list)):
                for j in range(i + 1, len(face_list)):
                    adjacency_list[face_list[i]].append(face_list[j])
                    adjacency_list[face_list[j]].append(face_list[i])

        mask = global_color_settings.get_mask()
        visited_faces = set()
        for face_index in range(len(obj.data.polygons)):
            if face_index not in visited_faces:
                connected_faces = get_connected_faces(face_index, visited_faces, adjacency_list)
                random_color = get_random_color(random_color_tool.color_mode, palette=palette)

                for connected_face_index in connected_faces:
                    poly = obj.data.polygons[connected_face_index]
                    for loop_index in poly.loop_indices:
                        data = color_attribute.data[loop_index]
                        data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def execute(self, context):
        scene = context.scene
        random_color_tool = scene.more_colors_random_color_tool
        global_color_settings = scene.more_colors_global_color_settings

        palette = [
            random_color_tool.palette_color_1,
            random_color_tool.palette_color_2,
            random_color_tool.palette_color_3,
            random_color_tool.palette_color_4,
        ]

        mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]

        if random_color_tool.element_type == "Object":
            self._apply_per_object(mesh_objects, global_color_settings, random_color_tool, palette)
        else:
            self._apply_per_element(mesh_objects, global_color_settings, random_color_tool, palette)

        self.report({"INFO"}, "Random vertex color applied!")
        return {"FINISHED"}

    def _apply_per_object(self, mesh_objects, global_color_settings, random_color_tool, palette):
        colors = get_distinct_random_colors(
            len(mesh_objects), random_color_tool.color_mode, palette=palette
        )
        mask = global_color_settings.get_mask()

        for obj, color in zip(mesh_objects, colors):
            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)
                for data in color_attribute.data:
                    data.color_srgb = get_masked_color(data.color_srgb, color, mask)

                obj.data.update()

    def _apply_per_element(self, mesh_objects, global_color_settings, random_color_tool, palette):
        for obj in mesh_objects:
            with ensure_object_mode(obj):
                self._color_single_object(obj, global_color_settings, random_color_tool, palette)

    def _color_single_object(self, obj, global_color_settings, random_color_tool, palette):
        color_attribute = get_active_color_attribute(obj)

        match color_attribute.domain:
            # On point domain color is stored per point, not per corner,
            # so element_type selection doesn't apply
            case "POINT":
                mask = global_color_settings.get_mask()
                for p in obj.data.vertices:
                    data = color_attribute.data[p.index]
                    random_color = get_random_color(random_color_tool.color_mode, palette=palette)
                    data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

            case "CORNER":
                match random_color_tool.element_type:
                    case "Point":
                        self.add_random_color_per_point(
                            obj, color_attribute, global_color_settings, random_color_tool, palette)
                    case "Vertex":
                        self.add_random_color_per_vertex(
                            color_attribute, global_color_settings, random_color_tool, palette)
                    case "Face":
                        self.add_random_color_per_face(
                            obj, color_attribute, global_color_settings, random_color_tool, palette)
                    case "Island":
                        self.add_random_color_per_island(
                            obj, color_attribute, global_color_settings, random_color_tool, palette)

        obj.data.update()
