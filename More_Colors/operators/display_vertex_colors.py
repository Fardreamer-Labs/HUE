# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .base_operators import BaseOperator


class MC_OT_display_vertex_colors(BaseOperator):
    """Toggles vertex color display mode in the viewport"""

    bl_label = "Display Vertex Colors"
    bl_idname = "morecolors.display_vertex_colors"

    def execute(self, context):
        settings = context.scene.more_colors_display_settings

        match settings.display_mode:
            case "Off":
                self.hide_vertex_colors(context)
            case "RGB":
                self.display_vertex_colors_as_rgb(context)
            case "Alpha":
                self.display_vertex_colors_as_alpha(context)

        return {"FINISHED"}

    def hide_vertex_colors(self, context):
        self.restore_scene_shading_settings(context)
        self.remove_alpha_display_material_from_all_mesh_objects(context)

    def display_vertex_colors_as_rgb(self, context):
        self.save_scene_shading_settings(context)
        self.remove_alpha_display_material_from_all_mesh_objects(context)

        context.space_data.shading.type = "SOLID"
        context.space_data.shading.color_type = "VERTEX"
        context.space_data.shading.light = "FLAT"

    def display_vertex_colors_as_alpha(self, context):
        self.restore_scene_shading_settings(context)

        self.remove_alpha_display_material_from_all_mesh_objects(context)
        self.apply_alpha_display_material_to_active_mesh_object(context)

        context.space_data.shading.type = "MATERIAL"

    def save_scene_shading_settings(self, context):
        settings = context.scene.more_colors_display_settings

        settings.previous_shading_type = context.space_data.shading.type
        settings.previous_color_type = context.space_data.shading.color_type
        settings.previous_light_type = context.space_data.shading.light

    def restore_scene_shading_settings(self, context):
        settings = context.scene.more_colors_display_settings

        context.space_data.shading.type = settings.previous_shading_type
        context.space_data.shading.color_type = settings.previous_color_type
        context.space_data.shading.light = settings.previous_light_type

    def get_or_create_alpha_display_material(self, context):
        settings = context.scene.more_colors_display_settings
        material_name = settings.alpha_display_material_name

        material = bpy.data.materials.get(material_name)

        if material is not None:
            # Update color attribute layer's name
            if context.active_object is not None:
                obj = context.active_object
                nodes = material.node_tree.nodes
                color_attribute_node = nodes.get("Color Attribute")

                if obj.data.color_attributes.active_color is not None:
                    color_attribute_node.layer_name = obj.data.color_attributes.active_color.name

            return material

        material = bpy.data.materials.new(name=material_name)

        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        for node in nodes:
            nodes.remove(node)

        material_output = nodes.new(type="ShaderNodeOutputMaterial")
        color_attribute_node = nodes.new(type="ShaderNodeVertexColor")
        color_attribute_node.location = (-300, 0)

        # Default layer name
        color_attribute_layer_name = "Color"

        if context.active_object is not None:
            obj = context.active_object
            if obj.data.color_attributes.active_color is not None:
                color_attribute_layer_name = obj.data.color_attributes.active_color.name

        color_attribute_node.layer_name = color_attribute_layer_name

        links.new(color_attribute_node.outputs["Alpha"], material_output.inputs["Surface"])

        return material

    def apply_alpha_display_material_to_active_mesh_object(self, context):
        alpha_display_material = self.get_or_create_alpha_display_material(context)

        settings = context.scene.more_colors_display_settings
        material_name = settings.alpha_display_material_name

        obj = context.active_object

        if obj is not None and obj.type == "MESH":
            # Append material
            obj.data.materials.append(alpha_display_material)

            # Make material active
            new_material_index = obj.data.materials.find(material_name)
            obj.active_material_index = new_material_index
            obj.active_material = alpha_display_material

            # Assign material to geometry
            bpy.context.view_layer.objects.active = obj
            current_mode = bpy.context.object.mode

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.object.material_slot_assign()

            bpy.ops.object.mode_set(mode=current_mode)

    def remove_alpha_display_material_from_all_mesh_objects(self, context):
        settings = context.scene.more_colors_display_settings
        material_name = settings.alpha_display_material_name

        for obj in context.scene.objects:
            if obj.type == "MESH":
                for slot in obj.material_slots:
                    if slot.material and slot.material.name == material_name:
                        obj.data.materials.pop(index=obj.material_slots.find(material_name))
