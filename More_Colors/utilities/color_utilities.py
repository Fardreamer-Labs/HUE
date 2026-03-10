# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import colorsys
import random

import bpy


def get_random_color_by_RGBA():
    """Returns a tuple with 4 floats (RGBA), each float is a random between 0 and 1."""
    return (random.random(), random.random(), random.random(), random.random())


def get_random_color_by_hue():
    """
    Generates a random color in HSL space, with hue random 0-1,
    saturation 1, lightness 0.5. Converts to RGB and returns RGBA
    with a random alpha.
    """
    hue = random.random()
    r, g, b = colorsys.hls_to_rgb(hue, 0.5, 1)
    return (r, g, b, random.random())


def get_random_color(mode="RGBA"):
    """Returns a random RGBA tuple. Mode selects the generation algorithm."""
    match mode:
        case "RGBA":
            return get_random_color_by_RGBA()
        case "Hue":
            return get_random_color_by_hue()
        case "Palette":
            return get_color_from_palette()


def get_masked_color(old_color, new_color, mask=(True, True, True, True)):
    """Applies new_color to old_color using the per-channel mask."""
    result_color = [old_color[0], old_color[1], old_color[2], old_color[3]]

    if mask[0]:
        result_color[0] = new_color[0]
    if mask[1]:
        result_color[1] = new_color[1]
    if mask[2]:
        result_color[2] = new_color[2]
    if mask[3]:
        result_color[3] = new_color[3]

    return result_color


def get_active_color_attribute(obj):
    """
    Gets the active color attribute of *obj*.
    Creates a default FLOAT_COLOR/CORNER attribute if none exists.
    """
    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        color_attribute = obj.data.color_attributes.new(
            name="Color", type="FLOAT_COLOR", domain="CORNER"
        )

    return color_attribute


def get_color_from_palette():
    """Randomly selects a color from the 4-color palette."""
    scene = bpy.context.scene
    random_color_tool = scene.more_colors_random_color_tool

    palette = [
        random_color_tool.palette_color_1,
        random_color_tool.palette_color_2,
        random_color_tool.palette_color_3,
        random_color_tool.palette_color_4,
    ]
    return random.choice(palette)
