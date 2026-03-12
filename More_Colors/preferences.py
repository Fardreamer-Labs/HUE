# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty,
    FloatProperty, FloatVectorProperty, IntProperty,
)
from bpy.types import AddonPreferences, PropertyGroup

from .utilities.palette_utilities import SWATCH_COLS, get_color_icon

# ---------------------------------------------------------------------------
# Available operators (for keyboard-shortcut reference)
# ---------------------------------------------------------------------------

_SHORTCUT_OPERATORS = [
    ("Apply Fill", "morecolors.simple_fill"),
    ("Add Random Color", "morecolors.add_random_color"),
    ("Random Color Per Object", "morecolors.add_random_color_by_object"),
    ("Apply Gradient", "morecolors.add_color_by_position"),
    ("Smooth Colors", "morecolors.smooth_vertex_colors"),
    ("Reset Vertex Colors", "morecolors.reset_vertex_colors"),
    ("Color By Selection", "morecolors.color_by_selection"),
    ("Color Adjustments", "morecolors.color_adjustments"),
    ("Attribute Transfer", "morecolors.attribute_transfer"),
]


# ---------------------------------------------------------------------------
# Default palette color item
# ---------------------------------------------------------------------------

class DefaultPaletteColor(PropertyGroup):
    color: FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=3,
    )


# ---------------------------------------------------------------------------
# Palette edit operators
# ---------------------------------------------------------------------------

class MC_OT_add_default_palette_color(bpy.types.Operator):
    """Add a color to the default palette in preferences"""

    bl_label = "Add Default Palette Color"
    bl_idname = "morecolors.add_default_palette_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        item = prefs.default_palette_colors.add()
        item.color = (1.0, 1.0, 1.0)
        return {"FINISHED"}


class MC_OT_remove_default_palette_color(bpy.types.Operator):
    """Remove the last color from the default palette in preferences"""

    bl_label = "Remove Default Palette Color"
    bl_idname = "morecolors.remove_default_palette_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        colors = prefs.default_palette_colors
        if len(colors) > 0:
            colors.remove(len(colors) - 1)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Shared enum items (mirrored from property_groups to avoid circular imports)
# ---------------------------------------------------------------------------

_ELEMENT_TYPE_ITEMS = [
    ("Point", "Per Point", ""),
    ("Vertex", "Per Vertex", ""),
    ("Face", "Per Face", ""),
    ("Island", "Per Island", ""),
    ("FaceSet", "Per Face Set", ""),
    ("Object", "Per Object", ""),
]

_COLOR_MODE_ITEMS = [
    ("RGBA", "RGB", ""),
    ("Hue", "Hue", ""),
    ("Palette", "Palette", ""),
]

_GRADIENT_SOURCE_ITEMS = [
    ("POSITION", "Position", ""),
    ("DISTANCE", "Distance", ""),
    ("NOISE", "Noise", ""),
    ("CURVATURE", "Curvature", ""),
    ("WEIGHT", "Weight", ""),
    ("DIRTY", "Dirty Vertex Colors", ""),
    ("VALENCE", "Valence", ""),
    ("FACE_AREA", "Face Area", ""),
    ("EDGE_LENGTH_VAR", "Edge Length Variance", ""),
    ("FACE_QUALITY", "Face Quality", ""),
]

_SPACE_TYPE_ITEMS = [
    ("Local", "Local Space", ""),
    ("World", "World Space", ""),
]

_GRADIENT_DIRECTION_ITEMS = [
    ("X", "X Axis", ""),
    ("-X", "-X Axis", ""),
    ("Y", "Y Axis", ""),
    ("-Y", "-Y Axis", ""),
    ("Z", "Z Axis", ""),
    ("-Z", "-Z Axis", ""),
]

_DISTANCE_ORIGIN_ITEMS = [
    ("CURSOR", "3D Cursor", ""),
    ("OBJECT", "Object Origin", ""),
    ("WORLD", "World Origin", ""),
]

_SMOOTH_CONSTRAINT_ITEMS = [
    ("NONE", "None", ""),
    ("SHARP", "Sharp Edges", ""),
    ("SEAM", "UV Seams", ""),
    ("BOUNDARY", "Boundary", ""),
]

_ADJUSTMENT_OP_ITEMS = [
    ("LEVELS", "Levels", ""),
    ("BRIGHTNESS_CONTRAST", "Brightness / Contrast", ""),
    ("HUE_SATURATION", "Hue / Saturation", ""),
    ("INVERT", "Invert", ""),
    ("POSTERIZE", "Posterize", ""),
    ("BLEND", "Layer Blend", ""),
]

_TRANSFER_MODE_ITEMS = [
    ("NEAREST_VERTEX", "Nearest Vertex", ""),
    ("NEAREST_SURFACE", "Nearest Surface", ""),
    ("RAYCAST", "Raycast", ""),
]


# ---------------------------------------------------------------------------
# Addon Preferences
# ---------------------------------------------------------------------------

class MoreColorsPreferences(AddonPreferences):
    bl_idname = __package__

    # -- Section toggles --
    show_keybinds: BoolProperty(name="Keyboard Shortcuts", default=False)
    show_fill: BoolProperty(name="Fill Defaults", default=False)
    show_randomize: BoolProperty(name="Randomize Defaults", default=False)
    show_gradient: BoolProperty(name="Gradient Defaults", default=False)
    show_smooth: BoolProperty(name="Smooth Defaults", default=False)
    show_adjustments: BoolProperty(name="Color Adjustments Defaults", default=False)
    show_selection: BoolProperty(name="Selection Defaults", default=False)
    show_mask: BoolProperty(name="Color Mask Defaults", default=False)
    show_palette: BoolProperty(name="Default Palette", default=False)

    # -- Fill defaults --
    default_fill_color: FloatVectorProperty(
        name="Default Color",
        subtype="COLOR",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
    )

    # -- Randomize defaults --
    default_random_element_type: EnumProperty(
        name="Element",
        items=_ELEMENT_TYPE_ITEMS,
        default="Point",
    )
    default_random_color_mode: EnumProperty(
        name="Color Mode",
        items=_COLOR_MODE_ITEMS,
        default="RGBA",
    )

    # -- Gradient defaults --
    default_gradient_source: EnumProperty(
        name="Source",
        items=_GRADIENT_SOURCE_ITEMS,
        default="POSITION",
    )
    default_gradient_space: EnumProperty(
        name="Space",
        items=_SPACE_TYPE_ITEMS,
        default="World",
    )
    default_gradient_direction: EnumProperty(
        name="Direction",
        items=_GRADIENT_DIRECTION_ITEMS,
        default="Z",
    )
    default_distance_origin: EnumProperty(
        name="Origin",
        items=_DISTANCE_ORIGIN_ITEMS,
        default="CURSOR",
    )
    default_noise_scale: FloatProperty(
        name="Scale",
        default=1.0,
        min=0.01,
        soft_max=10.0,
    )
    default_noise_detail: IntProperty(
        name="Detail",
        default=2,
        min=0,
        max=16,
    )
    default_noise_seed: IntProperty(
        name="Seed",
        default=0,
        min=0,
    )

    # -- Smooth defaults --
    default_smooth_iterations: IntProperty(
        name="Iterations",
        default=1,
        min=1,
        max=50,
    )
    default_smooth_factor: FloatProperty(
        name="Factor",
        default=0.5,
        min=0.0,
        max=1.0,
    )
    default_smooth_constraint: EnumProperty(
        name="Constraint",
        items=_SMOOTH_CONSTRAINT_ITEMS,
        default="NONE",
    )

    # -- Color Adjustments defaults --
    default_adjustment_operation: EnumProperty(
        name="Operation",
        items=_ADJUSTMENT_OP_ITEMS,
        default="LEVELS",
    )

    # -- Attribute Transfer defaults --
    show_transfer: BoolProperty(name="Transfer Defaults", default=False)
    default_transfer_mode: EnumProperty(
        name="Mode",
        items=_TRANSFER_MODE_ITEMS,
        default="NEAREST_VERTEX",
    )

    # -- Selection defaults --
    default_selection_selected_color: FloatVectorProperty(
        name="Selected Color",
        subtype="COLOR",
        default=(0.0, 0.8, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
    )
    default_selection_unselected_color: FloatVectorProperty(
        name="Unselected Color",
        subtype="COLOR",
        default=(0.1, 0.1, 0.1, 1.0),
        min=0.0,
        max=1.0,
        size=4,
    )

    # -- Color Mask defaults --
    default_mask_r: BoolProperty(name="R", default=True)
    default_mask_g: BoolProperty(name="G", default=True)
    default_mask_b: BoolProperty(name="B", default=True)
    default_mask_a: BoolProperty(name="A", default=True)

    # -- Default palette --
    default_palette_colors: CollectionProperty(type=DefaultPaletteColor)

    # -----------------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------------

    def draw(self, context):
        layout = self.layout

        # -- Fill Defaults --
        self._draw_section_header(layout, "show_fill", "BRUSH_DATA", "Fill Defaults")
        if self.show_fill:
            box = layout.box()
            box.prop(self, "default_fill_color")

        # -- Randomize Defaults --
        self._draw_section_header(layout, "show_randomize", "SHADERFX", "Randomize Defaults")
        if self.show_randomize:
            box = layout.box()
            box.prop(self, "default_random_element_type")
            box.prop(self, "default_random_color_mode")

        # -- Gradient Defaults --
        self._draw_section_header(layout, "show_gradient", "COLORSET_08_VEC", "Gradient Defaults")
        if self.show_gradient:
            box = layout.box()
            box.prop(self, "default_gradient_source")
            box.prop(self, "default_gradient_space")
            box.prop(self, "default_gradient_direction")
            box.prop(self, "default_distance_origin")
            box.separator()
            box.label(text="Noise Parameters:")
            box.prop(self, "default_noise_scale")
            box.prop(self, "default_noise_detail")
            box.prop(self, "default_noise_seed")

        # -- Smooth Defaults --
        self._draw_section_header(layout, "show_smooth", "SMOOTHCURVE", "Smooth Defaults")
        if self.show_smooth:
            box = layout.box()
            box.prop(self, "default_smooth_constraint")
            box.prop(self, "default_smooth_iterations")
            box.prop(self, "default_smooth_factor", slider=True)

        # -- Color Adjustments Defaults --
        self._draw_section_header(layout, "show_adjustments", "BRUSH_DATA", "Color Adjustments Defaults")
        if self.show_adjustments:
            box = layout.box()
            box.prop(self, "default_adjustment_operation")

        # -- Attribute Transfer Defaults --
        self._draw_section_header(layout, "show_transfer", "BRUSH_DATA", "Transfer Defaults")
        if self.show_transfer:
            box = layout.box()
            box.prop(self, "default_transfer_mode")

        # -- Selection Defaults --
        self._draw_section_header(layout, "show_selection", "RESTRICT_SELECT_OFF", "Selection Defaults")
        if self.show_selection:
            box = layout.box()
            box.prop(self, "default_selection_selected_color")
            box.prop(self, "default_selection_unselected_color")

        # -- Color Mask Defaults --
        self._draw_section_header(layout, "show_mask", "COLOR", "Color Mask Defaults")
        if self.show_mask:
            box = layout.box()
            row = box.row(align=True)
            row.prop(self, "default_mask_r", toggle=True)
            row.prop(self, "default_mask_g", toggle=True)
            row.prop(self, "default_mask_b", toggle=True)
            row.prop(self, "default_mask_a", toggle=True)

        # -- Default Palette --
        self._draw_section_header(layout, "show_palette", "PALETTE", "Default Palette")
        if self.show_palette:
            box = layout.box()
            colors = self.default_palette_colors
            if len(colors) > 0:
                for i, pc in enumerate(colors):
                    if i % SWATCH_COLS == 0:
                        row = box.row(align=True)
                        row.alignment = 'LEFT'
                    icon_id = get_color_icon(*pc.color)
                    row.prop(pc, "color", text="", icon_value=icon_id)
            row = box.row(align=True)
            row.operator("morecolors.add_default_palette_color", icon="ADD", text="")
            if len(colors) > 0:
                row.operator("morecolors.remove_default_palette_color", icon="REMOVE", text="")

        # -- Keyboard Shortcuts --
        self._draw_section_header(layout, "show_keybinds", "KEYINGSET", "Keyboard Shortcuts")
        if self.show_keybinds:
            box = layout.box()
            box.label(text="Right-click any button in the More Colors panel", icon='INFO')
            box.label(text="and choose \"Assign Shortcut\" to bind a key.")
            box.separator()
            box.label(text="Available operators:")
            for label, idname in _SHORTCUT_OPERATORS:
                row = box.row()
                row.label(text=label, icon='DOT')
                row.label(text=idname)

    @staticmethod
    def _draw_section_header(layout, prop_name, icon, label):
        row = layout.row()
        row.prop(
            bpy.context.preferences.addons[__package__].preferences,
            prop_name,
            icon='DISCLOSURE_TRI_DOWN' if getattr(
                bpy.context.preferences.addons[__package__].preferences, prop_name
            ) else 'DISCLOSURE_TRI_RIGHT',
            text=label,
            emboss=False,
        )


# ---------------------------------------------------------------------------
# Startup defaults application
# ---------------------------------------------------------------------------

@bpy.app.handlers.persistent
def _apply_startup_defaults(_=None):
    """Apply preference defaults to scene tool properties.

    Registered as a persistent load_post handler and called
    once from register() via timer.
    """
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
    except KeyError:
        return

    scene = bpy.context.scene

    # Fill
    fill_tool = getattr(scene, "more_colors_simple_fill_tool", None)
    if fill_tool:
        fill_tool.selected_color = prefs.default_fill_color

    # Randomize
    random_tool = getattr(scene, "more_colors_random_color_tool", None)
    if random_tool:
        random_tool.element_type = prefs.default_random_element_type
        random_tool.color_mode = prefs.default_random_color_mode

    # Gradient
    gradient_tool = getattr(scene, "more_colors_color_by_position_tool", None)
    if gradient_tool:
        gradient_tool.gradient_source = prefs.default_gradient_source
        gradient_tool.space_type = prefs.default_gradient_space
        gradient_tool.gradient_direction = prefs.default_gradient_direction
        gradient_tool.distance_origin = prefs.default_distance_origin
        gradient_tool.noise_scale = prefs.default_noise_scale
        gradient_tool.noise_detail = prefs.default_noise_detail
        gradient_tool.noise_seed = prefs.default_noise_seed

    # Smooth
    smooth_tool = getattr(scene, "more_colors_smooth_tool", None)
    if smooth_tool:
        smooth_tool.iterations = prefs.default_smooth_iterations
        smooth_tool.factor = prefs.default_smooth_factor
        smooth_tool.constraint_mode = prefs.default_smooth_constraint

    # Color Adjustments
    adj_tool = getattr(scene, "more_colors_color_adjustments_tool", None)
    if adj_tool:
        adj_tool.operation = prefs.default_adjustment_operation

    # Attribute Transfer
    transfer_tool = getattr(scene, "more_colors_attribute_transfer_tool", None)
    if transfer_tool:
        transfer_tool.transfer_mode = prefs.default_transfer_mode

    # Selection
    selection_tool = getattr(scene, "more_colors_color_by_selection_tool", None)
    if selection_tool:
        selection_tool.selected_color = prefs.default_selection_selected_color
        selection_tool.unselected_color = prefs.default_selection_unselected_color

    # Color Mask
    mask_tool = getattr(scene, "more_colors_global_color_settings", None)
    if mask_tool:
        mask_tool.global_color_mask_r = prefs.default_mask_r
        mask_tool.global_color_mask_g = prefs.default_mask_g
        mask_tool.global_color_mask_b = prefs.default_mask_b
        mask_tool.global_color_mask_a = prefs.default_mask_a


def get_default_palette_colors():
    """Return the list of default palette colors from preferences.

    Falls back to hardcoded defaults if preferences aren't available or empty.
    """
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        colors = prefs.default_palette_colors
        if len(colors) > 0:
            return [tuple(pc.color) for pc in colors]
    except KeyError:
        pass
    return None


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = [
    DefaultPaletteColor,
    MC_OT_add_default_palette_color,
    MC_OT_remove_default_palette_color,
    MoreColorsPreferences,
]


def _populate_default_palette():
    """Populate the default palette CollectionProperty if it's empty (first install)."""
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
    except KeyError:
        return
    if len(prefs.default_palette_colors) == 0:
        from .utilities.palette_utilities import _DEFAULT_COLORS
        for color in _DEFAULT_COLORS:
            item = prefs.default_palette_colors.add()
            item.color = color


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(_populate_default_palette, first_interval=0)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
