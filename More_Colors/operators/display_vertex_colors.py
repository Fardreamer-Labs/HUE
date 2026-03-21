# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .base_operators import BaseOperator
from ..ui.settings_panel.display_settings_panel import MC_PT_display_settings_panel


def update_display(context):
    """Core display-mode logic, callable without an operator instance."""
    settings = context.scene.more_colors_display_settings

    match settings.display_mode:
        case "Off":
            _hide_vertex_colors(context)
        case "RGB":
            _display_vertex_colors_as_rgb(context)
        case "Alpha":
            _display_vertex_colors_as_alpha(context)


def _hide_vertex_colors(context):
    _restore_scene_shading_settings(context)
    _remove_alpha_display_material_from_all_mesh_objects(context)


def _display_vertex_colors_as_rgb(context):
    _save_scene_shading_settings(context)
    _remove_alpha_display_material_from_all_mesh_objects(context)

    context.space_data.shading.type = "SOLID"
    context.space_data.shading.color_type = "VERTEX"
    context.space_data.shading.light = "FLAT"


def _display_vertex_colors_as_alpha(context):
    _restore_scene_shading_settings(context)

    _remove_alpha_display_material_from_all_mesh_objects(context)
    _apply_alpha_display_material_to_active_mesh_object(context)

    context.space_data.shading.type = "MATERIAL"


def _save_scene_shading_settings(context):
    settings = context.scene.more_colors_display_settings

    settings.previous_shading_type = context.space_data.shading.type
    settings.previous_color_type = context.space_data.shading.color_type
    settings.previous_light_type = context.space_data.shading.light


def _restore_scene_shading_settings(context):
    settings = context.scene.more_colors_display_settings

    context.space_data.shading.type = settings.previous_shading_type
    context.space_data.shading.color_type = settings.previous_color_type
    context.space_data.shading.light = settings.previous_light_type


def _get_or_create_alpha_display_material(context):
    settings = context.scene.more_colors_display_settings
    material_name = settings.alpha_display_material_name

    material = bpy.data.materials.get(material_name)

    if material is not None:
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

    color_attribute_layer_name = "Color"

    if context.active_object is not None:
        obj = context.active_object
        if obj.data.color_attributes.active_color is not None:
            color_attribute_layer_name = obj.data.color_attributes.active_color.name

    color_attribute_node.layer_name = color_attribute_layer_name

    links.new(color_attribute_node.outputs["Alpha"], material_output.inputs["Surface"])

    return material


def _apply_alpha_display_material_to_active_mesh_object(context):
    alpha_display_material = _get_or_create_alpha_display_material(context)

    settings = context.scene.more_colors_display_settings
    material_name = settings.alpha_display_material_name

    obj = context.active_object

    if obj is not None and obj.type == "MESH":
        obj.data.materials.append(alpha_display_material)

        mat_index = obj.data.materials.find(material_name)
        obj.active_material_index = mat_index
        obj.active_material = alpha_display_material

        # Assign material to all faces via mesh data API
        for poly in obj.data.polygons:
            poly.material_index = mat_index
        obj.data.update()


def _remove_alpha_display_material_from_all_mesh_objects(context):
    settings = context.scene.more_colors_display_settings
    material_name = settings.alpha_display_material_name

    for obj in context.scene.objects:
        if obj.type == "MESH":
            for slot in obj.material_slots:
                if slot.material and slot.material.name == material_name:
                    obj.data.materials.pop(index=obj.material_slots.find(material_name))
                    break


class MC_OT_display_vertex_colors(BaseOperator):
    """Toggles vertex color display mode in the viewport"""

    bl_label = "Display Vertex Colors"
    bl_idname = "morecolors.display_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_display(context)
        return {"FINISHED"}


class MC_OT_enable_rgb_display(BaseOperator):
    bl_label = "Enable Attribute View"
    bl_description = f"Switches the viewport to show vertex colors (RGB mode), the same as clicking RGB in the {MC_PT_display_settings_panel.bl_label} panel"
    bl_idname = "morecolors.enable_rgb_display"
    bl_options = {'REGISTER'}

    def execute(self, context):
        settings = context.scene.more_colors_display_settings
        # Find a 3D viewport and apply with a proper context so the
        # display_mode update callback can set shading correctly.
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                with context.temp_override(area=area, space_data=area.spaces.active):
                    settings.display_mode = "RGB"
                break
        else:
            # No 3D viewport visible — set the mode anyway for when one opens.
            settings.display_mode = "RGB"
        return {"FINISHED"}
