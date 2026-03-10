# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import FloatVectorProperty
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

    preset_color_1: FloatVectorProperty(
        name="Preset Color 1",
        description="Choose a color",
        subtype="COLOR",
        default=(1.000, 0.050, 0.078, 1.000),
        min=0,
        max=1,
        size=4,
    )

    preset_color_2: FloatVectorProperty(
        name="Preset Color 2",
        description="Choose a color",
        subtype="COLOR",
        default=(1.000, 0.743, 0.050, 1.000),
        min=0,
        max=1,
        size=4,
    )

    preset_color_3: FloatVectorProperty(
        name="Preset Color 3",
        description="Choose a color",
        subtype="COLOR",
        default=(0.498, 0.788, 0.039, 1.000),
        min=0,
        max=1,
        size=4,
    )

    preset_color_4: FloatVectorProperty(
        name="Preset Color 4",
        description="Choose a color",
        subtype="COLOR",
        default=(0.038, 0.490, 0.768, 1.000),
        min=0,
        max=1,
        size=4,
    )
