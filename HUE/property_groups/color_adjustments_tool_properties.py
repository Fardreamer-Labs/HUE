# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


class ColorAdjustmentsToolProperties(PropertyGroup):
    operation: EnumProperty(
        name="Operation",
        description="Color adjustment to apply",
        items=[
            ("LEVELS", "Levels", "Remap value range with black/white points and gamma", "CURVE_RGB", 1),
            ("BRIGHTNESS_CONTRAST", "Brightness / Contrast",
             "Adjust overall brightness and contrast", "SUN_DISTANCE", 2),
            ("HUE_SATURATION", "Hue / Saturation",
             "Shift hue and adjust saturation and value", "COLOR", 3),
            ("INVERT", "Invert", "Invert color channels", "ARROW_LEFTRIGHT", 4),
            ("POSTERIZE", "Posterize", "Reduce number of color levels", "IPO_CONSTANT", 5),
            ("BLEND", "Layer Blend", "Blend another color attribute layer onto the active one", "NODE_COMPOSITING", 6),
        ],
        default="LEVELS",
    )

    # -- Levels --
    levels_input_black: FloatProperty(
        name="Input Black",
        description="Black point of the input range",
        default=0.0,
        min=0.0,
        max=1.0,
    )

    levels_input_white: FloatProperty(
        name="Input White",
        description="White point of the input range",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    levels_gamma: FloatProperty(
        name="Gamma",
        description="Midtone gamma correction",
        default=1.0,
        min=0.01,
        max=10.0,
    )

    levels_output_black: FloatProperty(
        name="Output Black",
        description="Black point of the output range",
        default=0.0,
        min=0.0,
        max=1.0,
    )

    levels_output_white: FloatProperty(
        name="Output White",
        description="White point of the output range",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    # -- Brightness / Contrast --
    brightness: FloatProperty(
        name="Brightness",
        description="Brightness offset",
        default=0.0,
        min=-1.0,
        max=1.0,
    )

    contrast: FloatProperty(
        name="Contrast",
        description="Contrast multiplier",
        default=0.0,
        min=-1.0,
        max=1.0,
    )

    # -- Hue / Saturation --
    hue_shift: FloatProperty(
        name="Hue",
        description="Hue rotation (0.5 = no change)",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    saturation: FloatProperty(
        name="Saturation",
        description="Saturation multiplier (1.0 = no change)",
        default=1.0,
        min=0.0,
        max=2.0,
    )

    value_adjust: FloatProperty(
        name="Value",
        description="Value multiplier (1.0 = no change)",
        default=1.0,
        min=0.0,
        max=2.0,
    )

    # -- Posterize --
    posterize_levels: IntProperty(
        name="Levels",
        description="Number of discrete color levels per channel",
        default=8,
        min=2,
        max=256,
    )

    # -- Layer Blend --
    blend_layer: StringProperty(
        name="Layer",
        description="Name of the color attribute layer to blend from",
        default="",
    )

    blend_mode: EnumProperty(
        name="Mode",
        description="How to combine the two layers",
        items=[
            ("MIX", "Mix", "Linear interpolation toward the blend layer"),
            ("MULTIPLY", "Multiply", "Multiply the two layers"),
            ("ADD", "Add", "Add the blend layer on top"),
            ("SUBTRACT", "Subtract", "Subtract the blend layer"),
            ("OVERLAY", "Overlay", "Overlay blend (contrast-enhancing)"),
            ("SCREEN", "Screen", "Screen blend (lightening)"),
        ],
        default="MIX",
    )

    blend_factor: FloatProperty(
        name="Factor",
        description="Strength of the blend operation",
        default=1.0,
        min=0.0,
        max=1.0,
    )
