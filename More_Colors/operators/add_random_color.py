# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utilities.color_utilities import get_masked_color, get_random_color, get_active_color_attribute
from .base_operators import BaseColorOperator


class MC_OT_add_random_color(BaseColorOperator):
    """Adds a random color per chosen element (point, vertex, face) for each selected mesh object"""

    bl_label = "Add Random Color"
    bl_idname = "morecolors.add_random_color"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        return context.object and context.object.mode == "OBJECT"

    def add_random_color_per_face(self, obj, color_attribute, global_color_settings, random_color_tool):
        mask = global_color_settings.get_mask()
        for poly in obj.data.polygons:
            random_color = get_random_color(random_color_tool.color_mode)
            for loop_index in poly.loop_indices:
                data = color_attribute.data[loop_index]
                data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_point(self, obj, color_attribute, global_color_settings, random_color_tool):
        # Build vertex -> loop indices map in O(L)
        vert_to_loops = {}
        for loop in obj.data.loops:
            vert_to_loops.setdefault(loop.vertex_index, []).append(loop.index)

        mask = global_color_settings.get_mask()
        for vert in obj.data.vertices:
            random_color = get_random_color(random_color_tool.color_mode)
            for loop_index in vert_to_loops.get(vert.index, []):
                data = color_attribute.data[loop_index]
                data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_vertex(self, color_attribute, global_color_settings, random_color_tool):
        mask = global_color_settings.get_mask()
        for data in color_attribute.data:
            random_color = get_random_color(random_color_tool.color_mode)
            data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_island(self, obj, color_attribute, global_color_settings, random_color_tool):
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
                random_color = get_random_color(random_color_tool.color_mode)

                for connected_face_index in connected_faces:
                    poly = obj.data.polygons[connected_face_index]
                    for loop_index in poly.loop_indices:
                        data = color_attribute.data[loop_index]
                        data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def execute(self, context):
        scene = context.scene
        random_color_tool = scene.more_colors_random_color_tool
        global_color_settings = scene.more_colors_global_color_settings

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            color_attribute = get_active_color_attribute(obj)
            mask = global_color_settings.get_mask()

            match color_attribute.domain:
                # On point domain color is stored per point, not per corner,
                # so element_type selection doesn't apply
                case "POINT":
                    for p in obj.data.vertices:
                        data = color_attribute.data[p.index]
                        random_color = get_random_color(random_color_tool.color_mode)
                        data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

                case "CORNER":
                    match random_color_tool.element_type:
                        case "Point":
                            self.add_random_color_per_point(
                                obj, color_attribute, global_color_settings, random_color_tool)
                        case "Vertex":
                            self.add_random_color_per_vertex(
                                color_attribute, global_color_settings, random_color_tool)
                        case "Face":
                            self.add_random_color_per_face(
                                obj, color_attribute, global_color_settings, random_color_tool)
                        case "Island":
                            self.add_random_color_per_island(
                                obj, color_attribute, global_color_settings, random_color_tool)

            obj.data.update()

        self.report({"INFO"}, "Random vertex color applied!")
        return {"FINISHED"}
