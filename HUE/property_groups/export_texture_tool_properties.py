# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup

# Reentrancy guard for the Width/Height link-ratio update callbacks below, keyed
# by id(property_group_instance). Needed because setting resolution_y from
# within resolution_x's update callback (and vice versa) would otherwise
# re-trigger the other callback and recurse.
_RESOLUTION_LINK_GUARD = set()


def _sync_linked_resolution(source, target, ratio_from_source):
    def _update(self, context):
        if not self.resolution_linked or self.link_ratio <= 0:
            return
        key = id(self)
        if key in _RESOLUTION_LINK_GUARD:
            return
        _RESOLUTION_LINK_GUARD.add(key)
        try:
            current = getattr(self, source)
            new_value = int(round(ratio_from_source(current, self.link_ratio)))
            new_value = max(64, min(16384, new_value))
            if new_value != getattr(self, target):
                setattr(self, target, new_value)
        finally:
            _RESOLUTION_LINK_GUARD.discard(key)
    return _update


def _update_resolution_linked(self, context):
    if self.resolution_linked and self.resolution_y > 0:
        self.link_ratio = self.resolution_x / self.resolution_y


class ExportTextureToolProperties(PropertyGroup):
    export_path: StringProperty(
        name="Save Location",
        description="Directory to save the exported texture into (blank = next to the .blend file)",
        subtype="DIR_PATH",
        default="",
    )

    export_name: StringProperty(
        name="Name",
        description=(
            "Name for the created texture and exported file, without extension "
            "(blank = auto-named from object and attribute)"
        ),
        default="",
    )

    resolution_x: IntProperty(
        name="Width",
        description="Width of the exported texture in pixels",
        default=1024,
        min=64,
        max=16384,
        update=_sync_linked_resolution(
            "resolution_x", "resolution_y", lambda x, ratio: x / ratio
        ),
    )

    resolution_y: IntProperty(
        name="Height",
        description="Height of the exported texture in pixels",
        default=1024,
        min=64,
        max=16384,
        update=_sync_linked_resolution(
            "resolution_y", "resolution_x", lambda y, ratio: y * ratio
        ),
    )

    resolution_linked: BoolProperty(
        name="Link Width/Height",
        description="Keep Width and Height locked to their current aspect ratio when either one changes",
        default=False,
        update=_update_resolution_linked,
    )

    link_ratio: FloatProperty(
        name="Locked Aspect Ratio",
        description="Internal: Width/Height ratio captured when Link Width/Height was enabled",
        default=1.0,
        options={"HIDDEN"},
    )

    margin: IntProperty(
        name="Margin",
        description="Pixels to bleed color past UV island edges, preventing seams",
        default=16,
        min=0,
        max=64,
    )

    color_depth: EnumProperty(
        name="Color Depth",
        description="Bit depth of the exported PNG",
        items=[
            ("8", "8-bit", "256 levels per channel — smaller file size"),
            (
                "16",
                "16-bit",
                "65536 levels per channel — recommended to avoid banding in smooth gradients",
            ),
        ],
        default="16",
    )

    colorspace: EnumProperty(
        name="Color Space",
        description="How the exported texture's colors should be interpreted",
        items=[
            ("sRGB", "sRGB", "Standard color texture (albedo/tint)"),
            (
                "Non-Color",
                "Non-Color",
                "Raw data texture (masks, blend weights). Skips color management on creation",
            ),
        ],
        default="sRGB",
    )

    auto_unwrap: BoolProperty(
        name="Auto Unwrap",
        description=(
            "Automatically UV-unwrap (Smart UV Project) the active object if it has no UV layer"
        ),
        default=True,
    )

    apply_material: BoolProperty(
        name="Apply Material",
        description=(
            "After creating the texture, also build a quick material with it plugged into "
            "Base Color and assign that material to the object"
        ),
        default=False,
    )

    generated_image_name: StringProperty(
        name="Generated Texture",
        description="Name of the Image data-block created by 'Make Texture', used by 'Export as PNG'",
        default="",
    )

    overwrite_existing: BoolProperty(
        name="Overwrite Existing File",
        description=(
            "Overwrite the file at Save Location if it already exists, instead of "
            "creating a new numbered file (e.g. _001, _002...)"
        ),
        default=False,
    )
