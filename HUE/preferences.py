# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty,
    FloatProperty, FloatVectorProperty, IntProperty, StringProperty,
)
from bpy.types import AddonPreferences, PropertyGroup

from .utilities.palette_utilities import SWATCH_COLS, get_color_icon

# ---------------------------------------------------------------------------
# Available operators (for keyboard-shortcut reference)
# ---------------------------------------------------------------------------

_SHORTCUT_OPERATORS = [
    ("Apply Fill", "hue.simple_fill"),
    ("Add Random Color", "hue.add_random_color"),
    ("Random Color Per Object", "hue.add_random_color_by_object"),
    ("Apply Gradient", "hue.add_color_by_position"),
    ("Smooth Colors", "hue.smooth_vertex_colors"),
    ("Reset Vertex Colors", "hue.reset_vertex_colors"),
    ("Color By Selection", "hue.color_by_selection"),
    ("Color Adjustments", "hue.color_adjustments"),
    ("Attribute Transfer", "hue.attribute_transfer"),
    ("Symmetrize Colors", "hue.symmetrize_vertex_colors"),
]


# ---------------------------------------------------------------------------
# Default palette color item
# ---------------------------------------------------------------------------

class DefaultPaletteColor(PropertyGroup):
    color: FloatVectorProperty(
        name="Color",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=3,
    )


# ---------------------------------------------------------------------------
# Palette edit operators
# ---------------------------------------------------------------------------

class HUE_OT_add_default_palette_color(bpy.types.Operator):
    """Add a color to the default palette in preferences"""

    bl_label = "Add Default Palette Color"
    bl_idname = "hue.add_default_palette_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        item = prefs.default_palette_colors.add()
        item.color = (1.0, 1.0, 1.0)
        return {"FINISHED"}


class HUE_OT_remove_default_palette_color(bpy.types.Operator):
    """Remove the last color from the default palette in preferences"""

    bl_label = "Remove Default Palette Color"
    bl_idname = "hue.remove_default_palette_color"
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

_NOISE_BASIS_ITEMS = [
    ("PERLIN_ORIGINAL", "Perlin (Original)", ""),
    ("PERLIN_NEW", "Perlin (Improved)", ""),
    ("VORONOI_F1", "Voronoi F1", ""),
    ("VORONOI_F2", "Voronoi F2", ""),
    ("VORONOI_F2F1", "Voronoi F2-F1", ""),
    ("VORONOI_CRACKLE", "Voronoi Crackle", ""),
    ("CELLNOISE", "Cell Noise", ""),
    ("BLENDER", "Blender", ""),
]

_NOISE_TYPE_ITEMS = [
    ("FBM", "fBm", ""),
    ("MULTIFRACTAL", "Multifractal", ""),
    ("RIDGED", "Ridged", ""),
    ("HETERO", "Hetero Terrain", ""),
    ("TURBULENCE", "Turbulence", ""),
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

_SYMMETRIZE_AXIS_ITEMS = [
    ("X", "X", ""),
    ("Y", "Y", ""),
    ("Z", "Z", ""),
]

_SYMMETRIZE_DIRECTION_ITEMS = [
    ("POSITIVE_TO_NEGATIVE", "+ to \u2212", ""),
    ("NEGATIVE_TO_POSITIVE", "\u2212 to +", ""),
]


# ---------------------------------------------------------------------------
# Keyboard Shortcuts Modal
# ---------------------------------------------------------------------------

class ShortcutEntry(PropertyGroup):
    idname: StringProperty(name="Operator ID")


class HUE_OT_show_keybinds(bpy.types.Operator):
    """Show available keyboard shortcut operators"""

    bl_label = "Keyboard Shortcuts"
    bl_idname = "hue.show_keybinds"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        entries = context.window_manager.hue_shortcut_entries
        entries.clear()
        for op_label, idname in _SHORTCUT_OPERATORS:
            entry = entries.add()
            entry.name = op_label
            entry.idname = idname
        return context.window_manager.invoke_popup(self, width=480)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Right-click any button in the HUE panel", icon='INFO')
        layout.label(text='and choose "Assign Shortcut" to bind a key.')
        layout.separator()
        layout.label(text="Available operators for manual context aware assignment:")
        for entry in context.window_manager.hue_shortcut_entries:
            row = layout.row(align=True)
            row.label(text=entry.name, icon='DOT')
            row.prop(entry, "idname", text="")

    def execute(self, context):
        return {'FINISHED'}


class HUE_OT_visibility_warning(bpy.types.Operator):
    """Vertex colors may not be visible in the current viewport"""

    bl_label = "Color Not Visible"
    bl_idname = "hue.visibility_warning"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Vertex colors may not be visible.", icon='INFO')
        layout.label(text="Enable vertex color display to see your changes.")
        layout.separator()
        layout.operator("hue.enable_rgb_display", text="Enable Attribute View", icon="HIDE_OFF")
        layout.separator()
        try:
            prefs = context.preferences.addons[__package__].preferences
            layout.prop(prefs, "suppress_visibility_warning", text="Don't warn me about this")
        except KeyError:
            pass

    def execute(self, context):
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Addon Preferences
# ---------------------------------------------------------------------------

class HUEPreferences(AddonPreferences):
    bl_idname = __package__

    # -- Active tab --
    active_tab: EnumProperty(
        items=[
            ("GENERAL", "General", "Global defaults and palette"),
            ("PAINT", "Paint Tools", "Fill, Randomize, Gradient, and Selection defaults"),
            ("ADJUST", "Adjust Tools", "Smooth, Adjustments, Transfer, and Symmetrize defaults"),
        ],
        default="GENERAL",
    )

    # -- Section toggles --
    show_fill: BoolProperty(name="Fill Defaults", default=False)
    show_randomize: BoolProperty(name="Randomize Defaults", default=False)
    show_gradient: BoolProperty(name="Gradient Defaults", default=False)
    show_smooth: BoolProperty(name="Smooth Defaults", default=False)
    show_adjustments: BoolProperty(name="Color Adjustments Defaults", default=False)
    show_selection: BoolProperty(name="Selection Defaults", default=False)
    show_mask: BoolProperty(name="Color Mask Defaults", default=False)
    show_palette: BoolProperty(name="Default Palette", default=False)
    show_symmetrize: BoolProperty(name="Symmetrize Defaults", default=False)

    # -- Fill defaults --
    default_fill_color: FloatVectorProperty(
        name="Default Color",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
    )
    default_quick_fill: BoolProperty(
        name="Quick Fill",
        description="When enabled, clicking a palette swatch immediately fills the object with that color",
        default=False,
    )
    suppress_visibility_warning: BoolProperty(
        name="Don't warn when colors aren't visible",
        description=(
            "Suppress the warning popup shown after tool operations when "
            "vertex colors can't be seen in the current viewport"
        ),
        default=False,
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
    default_noise_basis: EnumProperty(
        name="Basis",
        items=_NOISE_BASIS_ITEMS,
        default="PERLIN_ORIGINAL",
    )
    default_noise_type: EnumProperty(
        name="Type",
        items=_NOISE_TYPE_ITEMS,
        default="FBM",
    )
    default_noise_roughness: FloatProperty(
        name="Roughness",
        default=1.0,
        min=0.0,
        soft_max=2.0,
    )
    default_noise_lacunarity: FloatProperty(
        name="Lacunarity",
        default=2.0,
        min=0.01,
        soft_max=6.0,
    )
    default_noise_distortion: FloatProperty(
        name="Distortion",
        default=0.0,
        min=0.0,
        soft_max=10.0,
    )
    default_normalize_per_island: BoolProperty(
        name="Normalize Per Island",
        default=False,
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

    # -- Symmetrize defaults --
    default_symmetrize_axis: EnumProperty(
        name="Axis",
        items=_SYMMETRIZE_AXIS_ITEMS,
        default="X",
    )
    default_symmetrize_direction: EnumProperty(
        name="Direction",
        items=_SYMMETRIZE_DIRECTION_ITEMS,
        default="POSITIVE_TO_NEGATIVE",
    )
    default_symmetrize_threshold: FloatProperty(
        name="Threshold",
        default=0.001,
        min=0.0,
        max=1.0,
    )

    # -- Selection defaults --
    default_selection_selected_color: FloatVectorProperty(
        name="Selected Color",
        subtype="COLOR_GAMMA",
        default=(0.0, 0.8, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
    )
    default_selection_unselected_color: FloatVectorProperty(
        name="Unselected Color",
        subtype="COLOR_GAMMA",
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
        row = layout.row(align=True)
        row.scale_y = 1.1
        row.prop_enum(self, "active_tab", "GENERAL", icon="SETTINGS")
        row.prop_enum(self, "active_tab", "PAINT", icon="BRUSH_DATA")
        row.prop_enum(self, "active_tab", "ADJUST", icon="MODIFIER")
        layout.separator(factor=0.5)

        if self.active_tab == "GENERAL":
            self._draw_section_header(layout, "show_mask", "COLOR", "Color Mask Defaults")
            if self.show_mask:
                box = layout.box()
                row = box.row(align=True)
                row.prop(self, "default_mask_r", toggle=True)
                row.prop(self, "default_mask_g", toggle=True)
                row.prop(self, "default_mask_b", toggle=True)
                row.prop(self, "default_mask_a", toggle=True)

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
                row.operator("hue.add_default_palette_color", icon="ADD", text="")
                if len(colors) > 0:
                    row.operator("hue.remove_default_palette_color", icon="REMOVE", text="")

            layout.separator(factor=0.5)
            layout.operator("hue.show_keybinds", text="Keyboard Shortcuts", icon="QUESTION")
            layout.prop(self, "suppress_visibility_warning")

        elif self.active_tab == "PAINT":
            self._draw_section_header(layout, "show_fill", "BRUSH_DATA", "Fill Defaults")
            if self.show_fill:
                box = layout.box()
                box.prop(self, "default_fill_color")
                box.prop(self, "default_quick_fill")

            self._draw_section_header(layout, "show_randomize", "SHADERFX", "Randomize Defaults")
            if self.show_randomize:
                box = layout.box()
                box.prop(self, "default_random_element_type")
                box.prop(self, "default_random_color_mode")

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
                box.prop(self, "default_noise_basis")
                box.prop(self, "default_noise_type")
                box.prop(self, "default_noise_seed")
                box.prop(self, "default_noise_roughness")
                box.prop(self, "default_noise_lacunarity")
                box.prop(self, "default_noise_distortion")
                box.separator()
                box.prop(self, "default_normalize_per_island")

            self._draw_section_header(layout, "show_selection", "RESTRICT_SELECT_OFF", "Color By Selection Defaults")
            if self.show_selection:
                box = layout.box()
                box.prop(self, "default_selection_selected_color")
                box.prop(self, "default_selection_unselected_color")

        elif self.active_tab == "ADJUST":
            self._draw_section_header(layout, "show_smooth", "SMOOTHCURVE", "Smooth Defaults")
            if self.show_smooth:
                box = layout.box()
                box.prop(self, "default_smooth_constraint")
                box.prop(self, "default_smooth_iterations")
                box.prop(self, "default_smooth_factor", slider=True)

            self._draw_section_header(layout, "show_adjustments", "BRUSH_DATA", "Color Adjustments Defaults")
            if self.show_adjustments:
                box = layout.box()
                box.prop(self, "default_adjustment_operation")

            self._draw_section_header(layout, "show_transfer", "BRUSH_DATA", "Transfer Defaults")
            if self.show_transfer:
                box = layout.box()
                box.prop(self, "default_transfer_mode")

            self._draw_section_header(layout, "show_symmetrize", "MOD_MIRROR", "Symmetrize Defaults")
            if self.show_symmetrize:
                box = layout.box()
                box.prop(self, "default_symmetrize_axis")
                box.prop(self, "default_symmetrize_direction")
                box.prop(self, "default_symmetrize_threshold")

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
    fill_tool = getattr(scene, "hue_simple_fill_tool", None)
    if fill_tool:
        fill_tool.selected_color = prefs.default_fill_color
        fill_tool.quick_fill = prefs.default_quick_fill

    # Randomize
    random_tool = getattr(scene, "hue_random_color_tool", None)
    if random_tool:
        random_tool.element_type = prefs.default_random_element_type
        random_tool.color_mode = prefs.default_random_color_mode

    # Gradient
    gradient_tool = getattr(scene, "hue_color_by_position_tool", None)
    if gradient_tool:
        gradient_tool.gradient_source = prefs.default_gradient_source
        gradient_tool.space_type = prefs.default_gradient_space
        gradient_tool.gradient_direction = prefs.default_gradient_direction
        gradient_tool.distance_origin = prefs.default_distance_origin
        gradient_tool.noise_scale = prefs.default_noise_scale
        gradient_tool.noise_detail = prefs.default_noise_detail
        gradient_tool.noise_seed = prefs.default_noise_seed
        gradient_tool.noise_basis = prefs.default_noise_basis
        gradient_tool.noise_type = prefs.default_noise_type
        gradient_tool.noise_roughness = prefs.default_noise_roughness
        gradient_tool.noise_lacunarity = prefs.default_noise_lacunarity
        gradient_tool.noise_distortion = prefs.default_noise_distortion
        gradient_tool.normalize_per_island = prefs.default_normalize_per_island

    # Smooth
    smooth_tool = getattr(scene, "hue_smooth_tool", None)
    if smooth_tool:
        smooth_tool.iterations = prefs.default_smooth_iterations
        smooth_tool.factor = prefs.default_smooth_factor
        smooth_tool.constraint_mode = prefs.default_smooth_constraint

    # Color Adjustments
    adj_tool = getattr(scene, "hue_color_adjustments_tool", None)
    if adj_tool:
        adj_tool.operation = prefs.default_adjustment_operation

    # Attribute Transfer
    transfer_tool = getattr(scene, "hue_attribute_transfer_tool", None)
    if transfer_tool:
        transfer_tool.transfer_mode = prefs.default_transfer_mode

    # Symmetrize
    sym_tool = getattr(scene, "hue_symmetrize_tool", None)
    if sym_tool:
        sym_tool.axis = prefs.default_symmetrize_axis
        sym_tool.direction = prefs.default_symmetrize_direction
        sym_tool.threshold = prefs.default_symmetrize_threshold

    # Selection
    selection_tool = getattr(scene, "hue_color_by_selection_tool", None)
    if selection_tool:
        selection_tool.selected_color = prefs.default_selection_selected_color
        selection_tool.unselected_color = prefs.default_selection_unselected_color

    # Color Mask
    mask_tool = getattr(scene, "hue_global_color_settings", None)
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
    ShortcutEntry,
    HUE_OT_add_default_palette_color,
    HUE_OT_remove_default_palette_color,
    HUE_OT_show_keybinds,
    HUE_OT_visibility_warning,
    HUEPreferences,
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
    bpy.types.WindowManager.hue_shortcut_entries = CollectionProperty(type=ShortcutEntry)
    bpy.app.timers.register(_populate_default_palette, first_interval=0)


def unregister():
    del bpy.types.WindowManager.hue_shortcut_entries
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
