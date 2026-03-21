# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup


class SmoothToolProperties(PropertyGroup):
    constraint_mode: EnumProperty(
        name="Constraint",
        description="Limit smoothing across topology boundaries",
        items=[
            ("NONE", "None", "Smooth across all edges", "NONE", 0),
            ("SHARP", "Sharp Edges", "Don\u2019t smooth across sharp-marked edges", "SHARPCURVE", 1),
            ("SEAM", "UV Seams", "Don\u2019t smooth across UV seam edges", "UV", 2),
            ("BOUNDARY", "Boundary", "Don\u2019t smooth across boundary edges", "MESH_PLANE", 3),
        ],
        default="NONE",
    )

    iterations: IntProperty(
        name="Iterations",
        description="Number of smoothing passes",
        default=1,
        min=1,
        max=50,
    )

    factor: FloatProperty(
        name="Factor",
        description="Blend strength per pass (0 = no change, 1 = full neighbor average)",
        default=0.5,
        min=0.0,
        max=1.0,
    )
