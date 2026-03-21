# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import BoolProperty, FloatVectorProperty, IntProperty, PointerProperty
from bpy.types import PropertyGroup


class SimpleFillToolProperties(PropertyGroup):
    selected_color: FloatVectorProperty(
        name="Color",
        description="Choose a color",
        subtype="COLOR",
        default=(1, 1, 1, 1),
        min=0,
        max=1,
        size=4,
    )

    preset_palette: PointerProperty(
        type=bpy.types.Palette,
        name="Preset Palette",
        description="Palette of saved color presets",
    )

    active_preset_index: IntProperty(
        name="Active Preset Index",
        default=0,
    )

    quick_fill: BoolProperty(
        name="Quick Fill",
        description="When enabled, clicking a palette swatch immediately fills the object with that color",
        default=False,
    )
