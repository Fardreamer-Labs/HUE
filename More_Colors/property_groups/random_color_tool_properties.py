# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, FloatVectorProperty
from bpy.types import PropertyGroup


class RandomColorToolProperties(PropertyGroup):
    element_type: EnumProperty(
        name="Element",
        description="Elements to generate colors on",
        items=[
            ("Point", "Per Point", "Points are shared across faces", "DECORATE", 1),
            ("Vertex", "Per Vertex", "Vertices are unique per face", "VERTEXSEL", 2),
            ("Face", "Per Face", "Faces are well... faces", "SNAP_FACE", 3),
            ("Island", "Per Island", "All mesh parts that are connected", "FACE_MAPS", 4),
        ]
    )

    color_mode: EnumProperty(
        name="Random Color Mode",
        description="Color generation method",
        items=[
            ("RGBA", "RGB", "Randomizes color by RGBA values."),
            ("Hue", "Hue", "Randomizes color only by hue. Saturation and alpha will be 1, lightness will be 0.5"),
            ("Palette", "Palette", "Randomly selects colors from the 4-color palette"),
        ]
    )

    palette_color_1: FloatVectorProperty(
        name="Palette Color 1",
        description="Choose a color",
        subtype="COLOR",
        default=(1.000, 0.050, 0.078, 1.000),
        min=0,
        max=1,
        size=4,
    )

    palette_color_2: FloatVectorProperty(
        name="Palette Color 2",
        description="Choose a color",
        subtype="COLOR",
        default=(1.000, 0.743, 0.050, 1.000),
        min=0,
        max=1,
        size=4,
    )

    palette_color_3: FloatVectorProperty(
        name="Palette Color 3",
        description="Choose a color",
        subtype="COLOR",
        default=(0.498, 0.788, 0.039, 1.000),
        min=0,
        max=1,
        size=4,
    )

    palette_color_4: FloatVectorProperty(
        name="Palette Color 4",
        description="Choose a color",
        subtype="COLOR",
        default=(0.038, 0.490, 0.768, 1.000),
        min=0,
        max=1,
        size=4,
    )
