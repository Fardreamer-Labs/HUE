# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import colorsys
import random
from contextlib import contextmanager

import bpy


@contextmanager
def ensure_object_mode(obj):
    """Context manager that temporarily switches *obj* to Object mode if needed.

    Usage::

        with ensure_object_mode(obj):
            # work with mesh data ...
    """
    was_edit = (obj.mode == "EDIT")
    if was_edit:
        bpy.ops.object.mode_set(mode="OBJECT")
    try:
        yield
    finally:
        if was_edit:
            bpy.ops.object.mode_set(mode="EDIT")


def build_vertex_loop_map(obj):
    """Return a dict mapping vertex index to a list of loop indices in O(L)."""
    vert_to_loops = {}
    for loop in obj.data.loops:
        vert_to_loops.setdefault(loop.vertex_index, []).append(loop.index)
    return vert_to_loops


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


def get_random_color(mode="RGBA", palette=None):
    """Returns a random RGBA tuple. Mode selects the generation algorithm."""
    match mode:
        case "RGBA":
            return get_random_color_by_RGBA()
        case "Hue":
            return get_random_color_by_hue()
        case "Palette":
            return get_color_from_palette(palette)


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


def get_color_from_palette(palette):
    """Randomly selects a color from the given palette list."""
    return random.choice(palette)


def _color_distance(c1, c2):
    """Euclidean distance between two colors in RGB space (ignores alpha)."""
    return sum((c1[i] - c2[i]) ** 2 for i in range(3)) ** 0.5


def get_distinct_random_colors(count, mode="RGBA", palette=None, min_distance=0.3, max_attempts=100):
    """Generate a list of visually distinct random colors.

    Uses rejection sampling to ensure minimum RGB distance between colors.
    Falls back to the best candidate found if *min_distance* can't be met.
    """
    colors = []
    for _ in range(count):
        best_color = None
        best_min_dist = -1
        for _ in range(max_attempts):
            candidate = get_random_color(mode, palette=palette)
            if not colors:
                best_color = candidate
                break
            min_dist = min(_color_distance(candidate, c) for c in colors)
            if min_dist >= min_distance:
                best_color = candidate
                break
            if min_dist > best_min_dist:
                best_color = candidate
                best_min_dist = min_dist
        colors.append(best_color)
    return colors
