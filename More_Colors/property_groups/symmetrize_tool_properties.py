# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, FloatProperty
from bpy.types import PropertyGroup


class SymmetrizeToolProperties(PropertyGroup):
    axis: EnumProperty(
        name="Axis",
        description="Axis to mirror across",
        items=[
            ("X", "X", "Mirror across the X axis", 1),
            ("Y", "Y", "Mirror across the Y axis", 2),
            ("Z", "Z", "Mirror across the Z axis", 3),
        ],
        default="X",
    )

    direction: EnumProperty(
        name="Direction",
        description="Which side to copy from",
        items=[
            ("POSITIVE_TO_NEGATIVE", "+ to \u2212", "Copy from positive side to negative side"),
            ("NEGATIVE_TO_POSITIVE", "\u2212 to +", "Copy from negative side to positive side"),
        ],
        default="POSITIVE_TO_NEGATIVE",
    )

    threshold: FloatProperty(
        name="Threshold",
        description="Maximum distance to match mirrored vertices",
        default=0.001,
        min=0.0,
        max=1.0,
        precision=4,
        step=1,
    )
