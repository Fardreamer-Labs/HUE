# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import EnumProperty, PointerProperty
from bpy.types import PropertyGroup


_ELEMENT_TYPE_ITEMS = [
    ("Point", "Per Point", "Points are shared across faces", "DECORATE", 1),
    ("Vertex", "Per Vertex", "Vertices are unique per face", "VERTEXSEL", 2),
    ("Face", "Per Face", "Faces are well... faces", "SNAP_FACE", 3),
    ("Island", "Per Island", "All mesh parts that are connected", "FACE_MAPS", 4),
    ("FaceSet", "Per Face Set", "Groups defined by sculpt face sets", "FACE_MAPS", 5),
    ("Object", "Per Object", "Each selected object gets a unique random color", "OBJECT_DATA", 6),
]


class RandomColorToolProperties(PropertyGroup):
    element_type: EnumProperty(
        name="Element",
        description="Elements to generate colors on",
        items=_ELEMENT_TYPE_ITEMS,
    )

    color_mode: EnumProperty(
        name="Random Color Mode",
        description="Color generation method",
        items=[
            ("RGBA", "RGB", "Randomizes color by RGBA values."),
            ("Hue", "Hue", "Randomizes color only by hue. Saturation and alpha will be 1, lightness will be 0.5"),
            ("Palette", "Palette", "Randomly selects colors from a palette"),
        ]
    )

    random_palette: PointerProperty(
        type=bpy.types.Palette,
        name="Palette",
        description="Palette to randomly pick colors from",
    )
