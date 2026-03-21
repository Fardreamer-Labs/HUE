# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..utilities.palette_utilities import DEFAULT_PALETTE_NAME
from ..utilities.color_utilities import (
    apply_mask_constant, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute, get_selected_color_indices,
)
from .base_operators import BaseColorOperator, BaseOperator


def _apply_fill(obj, color, mask, select_mode):
    """Apply color fill using numpy bulk operations (requires object mode).

    When *select_mode* is ``None`` (object mode), all elements are colored.
    """
    color_attribute = get_active_color_attribute(obj)
    indices = get_selected_color_indices(obj, select_mode, color_attribute.domain)
    colors = bulk_get_colors(color_attribute)
    apply_mask_constant(colors, color, mask, indices)
    bulk_set_colors(color_attribute, colors)
    obj.data.update()


def execute_simple_fill(context):
    """Core simple fill logic, callable without an operator instance.

    Returns (success, message) tuple.
    """
    scene = context.scene
    global_color_settings = scene.hue_global_color_settings
    simple_fill_tool = scene.hue_simple_fill_tool
    mask = global_color_settings.get_mask()
    color = simple_fill_tool.selected_color
    select_mode = context.tool_settings.mesh_select_mode if context.mode == 'EDIT_MESH' else None

    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue

        with ensure_object_mode(obj):
            _apply_fill(obj, color, mask, select_mode)

    return True, "Vertex colors assigned successfully!"


class HUE_OT_simple_fill(BaseColorOperator):
    """Applies a selected color to selected object(s) or part of the mesh"""

    bl_label = "Apply Color"
    bl_idname = "hue.simple_fill"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success, msg = execute_simple_fill(context)
        if not success:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class HUE_OT_add_preset_color(BaseOperator):
    """Saves the current active color as a new color preset"""

    bl_label = "Add Preset Color"
    bl_idname = "hue.add_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        simple_fill_tool = context.scene.hue_simple_fill_tool
        palette = simple_fill_tool.preset_palette
        if not palette:
            palette = bpy.data.palettes.get("HUE_SimpleFillPresets")
            if not palette:
                palette = bpy.data.palettes.new("HUE_SimpleFillPresets")
            simple_fill_tool.preset_palette = palette
        color = simple_fill_tool.selected_color
        new_color = palette.colors.new()
        new_color.color = (color[0], color[1], color[2])
        simple_fill_tool.active_preset_index = len(palette.colors) - 1
        return {"FINISHED"}


class HUE_OT_remove_preset_color(BaseOperator):
    """Removes the currently selected color preset"""

    bl_label = "Remove Preset Color"
    bl_idname = "hue.remove_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        simple_fill_tool = context.scene.hue_simple_fill_tool
        palette = simple_fill_tool.preset_palette
        if not palette or len(palette.colors) == 0:
            self.report({"WARNING"}, "No preset colors to remove")
            return {"CANCELLED"}
        idx = simple_fill_tool.active_preset_index
        idx = min(idx, len(palette.colors) - 1)
        palette.colors.remove(palette.colors[idx])
        if len(palette.colors) > 0:
            simple_fill_tool.active_preset_index = min(idx, len(palette.colors) - 1)
        else:
            simple_fill_tool.active_preset_index = 0
        return {"FINISHED"}


class HUE_OT_new_palette(BaseOperator):
    """Creates a new color palette"""

    bl_label = "New Palette"
    bl_idname = "hue.new_palette"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        palette = bpy.data.palettes.new("Palette")
        tool = context.scene.hue_simple_fill_tool
        tool.preset_palette = palette
        tool.active_preset_index = 0
        return {"FINISHED"}


class HUE_OT_rename_palette(BaseOperator):
    """Renames the currently selected palette"""

    bl_label = "Rename Palette"
    bl_idname = "hue.rename_palette"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, event):
        palette = context.scene.hue_simple_fill_tool.preset_palette
        if not palette:
            self.report({"WARNING"}, "No palette selected")
            return {"CANCELLED"}
        if palette.name == DEFAULT_PALETTE_NAME:
            self.report({"WARNING"}, "Cannot rename the default palette!")
            return {"CANCELLED"}
        self.new_name = palette.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "new_name", text="")

    def execute(self, context):
        palette = context.scene.hue_simple_fill_tool.preset_palette
        if not palette:
            return {"CANCELLED"}
        if not self.new_name.strip():
            self.report({"WARNING"}, "Name cannot be empty")
            return {"CANCELLED"}
        palette.name = self.new_name.strip()
        return {"FINISHED"}


class HUE_OT_delete_palette(BaseOperator):
    """Deletes the currently selected palette"""

    bl_label = "Delete Palette"
    bl_idname = "hue.delete_palette"
    bl_options = {'REGISTER', 'UNDO'}

    palette_name: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def invoke(self, context, event):
        palette = context.scene.hue_simple_fill_tool.preset_palette
        if not palette:
            self.report({"WARNING"}, "No palette selected")
            return {"CANCELLED"}
        if palette.name == DEFAULT_PALETTE_NAME:
            self.report({"WARNING"}, "Cannot delete the default palette!")
            return {"CANCELLED"}
        self.palette_name = palette.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=f"Delete \"{self.palette_name}\" palette?")

    def execute(self, context):
        tool = context.scene.hue_simple_fill_tool
        palette = tool.preset_palette
        if not palette:
            self.report({"WARNING"}, "No palette selected")
            return {"CANCELLED"}
        if palette.name == DEFAULT_PALETTE_NAME:
            self.report({"WARNING"}, "Cannot delete the default palette!")
            return {"CANCELLED"}
        tool.preset_palette = None
        bpy.data.palettes.remove(palette)
        return {"FINISHED"}


class HUE_OT_use_preset_color(BaseOperator):
    """Selects this preset and sets it as the active color. With Quick Fill enabled, also immediately fills the object."""

    warn_visibility_check = False

    bl_label = "Use Preset Color"
    bl_idname = "hue.use_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        simple_fill_tool = context.scene.hue_simple_fill_tool
        palette = simple_fill_tool.preset_palette
        if not palette or self.index >= len(palette.colors):
            return {"CANCELLED"}
        color = palette.colors[self.index].color
        simple_fill_tool.selected_color[0] = color[0]
        simple_fill_tool.selected_color[1] = color[1]
        simple_fill_tool.selected_color[2] = color[2]
        simple_fill_tool.active_preset_index = self.index

        if simple_fill_tool.quick_fill:
            success, msg = execute_simple_fill(context)
            if not success:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
            self.report({"INFO"}, msg)

        return {"FINISHED"}
