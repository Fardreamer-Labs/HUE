# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


class ColorByPositionToolProperties(PropertyGroup):
    gradient_source: EnumProperty(
        name="Source",
        description="Data source for the gradient",
        items=[
            ("POSITION", "Position", "Map vertex position along an axis", "EMPTY_AXIS", 1),
            ("DISTANCE", "Distance", "Radial gradient from a reference point", "DRIVER_DISTANCE", 2),
            ("NOISE", "Noise", "Perlin noise pattern", "FORCE_TURBULENCE", 3),
            ("CURVATURE", "Curvature", "Surface curvature (convex vs concave)", "SMOOTHCURVE", 4),
            ("WEIGHT", "Weight", "Active vertex group weights", "GROUP_VERTEX", 5),
        ],
        default="POSITION",
    )

    space_type: EnumProperty(
        name="Space",
        description="Coordinate space for computing the gradient",
        items=[
            ("Local", "Local Space", "", "ORIENTATION_LOCAL", 1),
            ("World", "World Space", "", "WORLD", 2),
        ],
        default="World",
    )

    gradient_direction: EnumProperty(
        name="Direction",
        description="Axis and direction for the gradient",
        items=[
            ("X", "X Axis", ""),
            ("-X", "-X Axis", ""),
            ("Y", "Y Axis", ""),
            ("-Y", "-Y Axis", ""),
            ("Z", "Z Axis", ""),
            ("-Z", "-Z Axis", ""),
        ],
        default="Z",
    )

    distance_origin: EnumProperty(
        name="Origin",
        description="Center point for the radial gradient",
        items=[
            ("CURSOR", "3D Cursor", "", "PIVOT_CURSOR", 1),
            ("OBJECT", "Object Origin", "", "OBJECT_DATA", 2),
            ("WORLD", "World Origin", "", "WORLD", 3),
        ],
        default="CURSOR",
    )

    noise_scale: FloatProperty(
        name="Scale",
        description="Scale of the noise pattern",
        default=1.0,
        min=0.01,
        soft_max=10.0,
    )

    noise_detail: IntProperty(
        name="Detail",
        description="Number of noise octaves",
        default=2,
        min=0,
        max=16,
    )

    noise_seed: IntProperty(
        name="Seed",
        description="Random seed for the noise offset",
        default=0,
        min=0,
    )

    color_ramp_material_name: StringProperty(
        name="Color Ramp Material Name",
        default="MORECOLORS_ColorByPositionRamp",
    )
