# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import random

import numpy as np
from bpy.props import EnumProperty, IntProperty

from ..utilities.color_utilities import (
    apply_mask_constant, build_vertex_loop_map, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute, get_distinct_random_colors,
    get_random_color, get_selected_color_indices,
)
from .base_operators import BaseColorOperator


class MC_OT_add_random_color(BaseColorOperator):
    """Adds a random color per chosen element (point, vertex, face) for each selected mesh object"""

    bl_label = "Add Random Color"
    bl_idname = "morecolors.add_random_color"
    bl_options = {'REGISTER', 'UNDO'}

    seed: IntProperty(
        name="Seed",
        description="Random seed for reproducible results",
        default=0,
        min=0,
    )

    element_type: EnumProperty(
        name="Element",
        description="Elements to generate colors on",
        items=[
            ("Point", "Per Point", "Points are shared across faces"),
            ("Vertex", "Per Vertex", "Vertices are unique per face"),
            ("Face", "Per Face", "Faces are well... faces"),
            ("Island", "Per Island", "All mesh parts that are connected"),
            ("FaceSet", "Per Face Set", "Groups defined by sculpt face sets"),
            ("Object", "Per Object", "Each selected object gets a unique random color"),
        ],
    )

    color_mode: EnumProperty(
        name="Color Mode",
        description="Color generation method",
        items=[
            ("RGBA", "RGB", "Randomizes color by RGBA values."),
            ("Hue", "Hue", "Randomizes color only by hue"),
            ("Palette", "Palette", "Randomly selects colors from a palette"),
        ],
    )

    def invoke(self, context, event):
        tool = context.scene.more_colors_random_color_tool
        self.element_type = tool.element_type
        self.color_mode = tool.color_mode
        self.seed = random.randint(0, 99999)
        result = self.execute(context)
        if result == {'FINISHED'}:
            self._maybe_warn_visibility(context)
        return result

    def add_random_color_per_face(self, obj, color_attribute, global_color_settings,
                                  palette, selected_only=True):
        mask = global_color_settings.get_mask()
        colors = bulk_get_colors(color_attribute)
        for poly in obj.data.polygons:
            if selected_only and not poly.select:
                continue
            rc = get_random_color(self.color_mode, palette=palette)
            loop_arr = np.arange(poly.loop_start, poly.loop_start + poly.loop_total, dtype=np.intp)
            apply_mask_constant(colors, rc, mask, loop_arr)
        bulk_set_colors(color_attribute, colors)

    def add_random_color_per_point(self, obj, color_attribute, global_color_settings,
                                   palette, selected_only=True):
        vert_to_loops = build_vertex_loop_map(obj)
        mask = global_color_settings.get_mask()
        colors = bulk_get_colors(color_attribute)
        for vert in obj.data.vertices:
            if selected_only and not vert.select:
                continue
            rc = get_random_color(self.color_mode, palette=palette)
            loops = vert_to_loops.get(vert.index, [])
            if loops:
                apply_mask_constant(colors, rc, mask, np.array(loops, dtype=np.intp))
        bulk_set_colors(color_attribute, colors)

    def add_random_color_per_vertex(self, obj, color_attribute, global_color_settings,
                                    palette, select_mode):
        mask = global_color_settings.get_mask()
        colors = bulk_get_colors(color_attribute)
        indices = get_selected_color_indices(obj, select_mode, "CORNER")
        target = np.arange(len(colors), dtype=np.intp) if indices is None else indices
        for li in target:
            rc = get_random_color(self.color_mode, palette=palette)
            for ch in range(4):
                if mask[ch]:
                    colors[li, ch] = rc[ch]
        bulk_set_colors(color_attribute, colors)

    def add_random_color_per_island(self, obj, color_attribute, global_color_settings,
                                    palette, selected_only=True):
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

        # Determine which faces to consider
        if selected_only:
            candidate_faces = {
                i for i, poly in enumerate(obj.data.polygons) if poly.select
            }
        else:
            candidate_faces = set(range(len(obj.data.polygons)))

        # Build edge_key -> face list from candidate faces
        edge_to_faces = {}
        for poly_index in candidate_faces:
            poly = obj.data.polygons[poly_index]
            for edge_key in poly.edge_keys:
                edge_to_faces.setdefault(edge_key, []).append(poly_index)

        # Build adjacency from edge_to_faces
        adjacency_list = {i: [] for i in candidate_faces}
        for face_list in edge_to_faces.values():
            for i in range(len(face_list)):
                for j in range(i + 1, len(face_list)):
                    adjacency_list[face_list[i]].append(face_list[j])
                    adjacency_list[face_list[j]].append(face_list[i])

        mask = global_color_settings.get_mask()
        colors = bulk_get_colors(color_attribute)
        visited_faces = set()
        for face_index in candidate_faces:
            if face_index not in visited_faces:
                connected_faces = get_connected_faces(face_index, visited_faces, adjacency_list)
                rc = get_random_color(self.color_mode, palette=palette)

                island_loops = []
                for cfi in connected_faces:
                    poly = obj.data.polygons[cfi]
                    island_loops.extend(poly.loop_indices)
                apply_mask_constant(colors, rc, mask, np.array(island_loops, dtype=np.intp))
        bulk_set_colors(color_attribute, colors)

    def add_random_color_per_face_set(self, obj, color_attribute, global_color_settings,
                                      palette, selected_only=True):
        face_set_attr = obj.data.attributes.get(".sculpt_face_set")
        if face_set_attr is None:
            return False

        # Group face indices by face set ID
        face_sets = {}
        for i, poly in enumerate(obj.data.polygons):
            if selected_only and not poly.select:
                continue
            fs_id = face_set_attr.data[i].value
            face_sets.setdefault(fs_id, []).append(i)

        mask = global_color_settings.get_mask()
        colors = bulk_get_colors(color_attribute)
        for face_indices in face_sets.values():
            rc = get_random_color(self.color_mode, palette=palette)
            set_loops = []
            for fi in face_indices:
                poly = obj.data.polygons[fi]
                set_loops.extend(poly.loop_indices)
            apply_mask_constant(colors, rc, mask, np.array(set_loops, dtype=np.intp))
        bulk_set_colors(color_attribute, colors)
        return True

    def execute(self, context):
        random.seed(self.seed)
        scene = context.scene
        random_color_tool = scene.more_colors_random_color_tool
        global_color_settings = scene.more_colors_global_color_settings
        in_edit = context.mode == 'EDIT_MESH'
        select_mode = context.tool_settings.mesh_select_mode if in_edit else None

        palette = None
        if self.color_mode == "Palette":
            if not random_color_tool.random_palette or len(random_color_tool.random_palette.colors) == 0:
                self.report({"ERROR"}, "Palette is empty. Add colors to the palette first.")
                return {"CANCELLED"}
            palette = [(*pc.color, 1.0) for pc in random_color_tool.random_palette.colors]

        mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]

        if self.element_type == "Object":
            self._apply_per_object(mesh_objects, global_color_settings, palette)
        else:
            self._apply_per_element(
                mesh_objects, global_color_settings, palette, select_mode)

        self.report({"INFO"}, "Random vertex color applied!")
        return {"FINISHED"}

    def _apply_per_object(self, mesh_objects, global_color_settings, palette):
        distinct = get_distinct_random_colors(
            len(mesh_objects), self.color_mode, palette=palette
        )
        mask = global_color_settings.get_mask()

        for obj, color in zip(mesh_objects, distinct):
            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)
                colors = bulk_get_colors(color_attribute)
                apply_mask_constant(colors, color, mask)
                bulk_set_colors(color_attribute, colors)
                obj.data.update()

    def _apply_per_element(self, mesh_objects, global_color_settings,
                           palette, select_mode):
        for obj in mesh_objects:
            with ensure_object_mode(obj):
                self._color_single_object(
                    obj, global_color_settings, palette, select_mode)

    def _color_single_object(self, obj, global_color_settings,
                             palette, select_mode):
        color_attribute = get_active_color_attribute(obj)
        selected_only = select_mode is not None

        match color_attribute.domain:
            case "POINT":
                mask = global_color_settings.get_mask()
                colors = bulk_get_colors(color_attribute)
                indices = get_selected_color_indices(obj, select_mode, "POINT")
                target = np.arange(len(colors), dtype=np.intp) if indices is None else indices
                for vi in target:
                    rc = get_random_color(self.color_mode, palette=palette)
                    for ch in range(4):
                        if mask[ch]:
                            colors[vi, ch] = rc[ch]
                bulk_set_colors(color_attribute, colors)

            case "CORNER":
                match self.element_type:
                    case "Point":
                        self.add_random_color_per_point(
                            obj, color_attribute, global_color_settings,
                            palette, selected_only)
                    case "Vertex":
                        self.add_random_color_per_vertex(
                            obj, color_attribute, global_color_settings,
                            palette, select_mode)
                    case "Face":
                        self.add_random_color_per_face(
                            obj, color_attribute, global_color_settings,
                            palette, selected_only)
                    case "Island":
                        self.add_random_color_per_island(
                            obj, color_attribute, global_color_settings,
                            palette, selected_only)
                    case "FaceSet":
                        if not self.add_random_color_per_face_set(
                            obj, color_attribute, global_color_settings,
                            palette, selected_only
                        ):
                            self.report({"ERROR"}, "No face sets found. Use Sculpt Mode to create face sets.")
                            return

        obj.data.update()


class MC_OT_add_random_color_by_object(BaseColorOperator):
    """Assigns a unique random color to each selected mesh object"""

    bl_label = "Add Random Color Per Object"
    bl_idname = "morecolors.add_random_color_by_object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        random_color_tool = scene.more_colors_random_color_tool
        global_color_settings = scene.more_colors_global_color_settings

        palette = None
        if random_color_tool.random_palette and len(random_color_tool.random_palette.colors) > 0:
            palette = [
                (*pc.color, 1.0) for pc in random_color_tool.random_palette.colors
            ]

        mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]

        colors = get_distinct_random_colors(
            len(mesh_objects), random_color_tool.color_mode, palette=palette
        )
        mask = global_color_settings.get_mask()

        for obj, color in zip(mesh_objects, colors):
            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)
                all_colors = bulk_get_colors(color_attribute)
                apply_mask_constant(all_colors, color, mask)
                bulk_set_colors(color_attribute, all_colors)
                obj.data.update()

        self.report({"INFO"}, "Random color per object applied!")
        return {"FINISHED"}
