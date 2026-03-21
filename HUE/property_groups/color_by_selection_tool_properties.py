# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import FloatVectorProperty
from bpy.types import PropertyGroup


class ColorBySelectionToolProperties(PropertyGroup):
    selected_color: FloatVectorProperty(
        name="Selected",
        description="Color applied to selected elements",
        subtype="COLOR",
        default=(0.0, 0.8, 1.0, 1.0),
        min=0,
        max=1,
        size=4,
    )

    unselected_color: FloatVectorProperty(
        name="Unselected",
        description="Color applied to unselected elements",
        subtype="COLOR",
        default=(0.1, 0.1, 0.1, 1.0),
        min=0,
        max=1,
        size=4,
    )
