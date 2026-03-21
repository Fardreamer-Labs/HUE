# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for utilities/palette_utilities.py.

Runs inside Blender via::

    blender -b --factory-startup -P Tests/conftest.py --python-exit-code 1
"""

import sys
import unittest
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent
_addon_root = _tests_dir.parent / "More_Colors"
for p in (_tests_dir, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import bpy

from utilities.palette_utilities import (
    DEFAULT_PALETTE_NAME,
    _linear_to_srgb,
    cleanup_previews,
    get_color_icon,
    get_or_create_default_palette,
)


class TestLinearToSrgb(unittest.TestCase):
    """Pure function — no Blender data needed."""

    def test_zero(self):
        self.assertAlmostEqual(_linear_to_srgb(0.0), 0.0)

    def test_one(self):
        self.assertAlmostEqual(_linear_to_srgb(1.0), 1.0)

    def test_low_linear_value(self):
        # Below 0.0031308 → linear region: c * 12.92
        self.assertAlmostEqual(_linear_to_srgb(0.001), 0.001 * 12.92, places=6)

    def test_mid_value(self):
        # 0.5 linear ≈ 0.735 sRGB (standard formula)
        result = _linear_to_srgb(0.5)
        expected = 1.055 * (0.5 ** (1.0 / 2.4)) - 0.055
        self.assertAlmostEqual(result, expected, places=6)

    def test_monotonic(self):
        """sRGB conversion should be monotonically increasing."""
        prev = _linear_to_srgb(0.0)
        for i in range(1, 101):
            val = i / 100.0
            curr = _linear_to_srgb(val)
            self.assertGreater(curr, prev)
            prev = curr


class TestGetOrCreateDefaultPalette(unittest.TestCase):
    def setUp(self):
        # Remove existing palette if present
        existing = bpy.data.palettes.get(DEFAULT_PALETTE_NAME)
        if existing:
            bpy.data.palettes.remove(existing)

    def tearDown(self):
        existing = bpy.data.palettes.get(DEFAULT_PALETTE_NAME)
        if existing:
            bpy.data.palettes.remove(existing)

    def test_creates_palette(self):
        palette = get_or_create_default_palette()
        self.assertIsNotNone(palette)
        self.assertEqual(palette.name, DEFAULT_PALETTE_NAME)

    def test_palette_has_colors(self):
        palette = get_or_create_default_palette()
        self.assertGreater(len(palette.colors), 0)

    def test_returns_same_palette_on_second_call(self):
        p1 = get_or_create_default_palette()
        p2 = get_or_create_default_palette()
        self.assertEqual(p1.name, p2.name)
        # Should not have duplicated colors
        self.assertEqual(len(p1.colors), len(p2.colors))

    def test_default_colors_are_valid_rgb(self):
        palette = get_or_create_default_palette()
        for pc in palette.colors:
            for ch in range(3):
                self.assertGreaterEqual(pc.color[ch], 0.0)
                self.assertLessEqual(pc.color[ch], 1.0)


class TestGetColorIcon(unittest.TestCase):
    def tearDown(self):
        cleanup_previews()

    def test_returns_int_icon_id(self):
        icon_id = get_color_icon(1.0, 0.0, 0.0)
        self.assertIsInstance(icon_id, int)

    def test_same_color_returns_same_id(self):
        id1 = get_color_icon(0.5, 0.5, 0.5)
        id2 = get_color_icon(0.5, 0.5, 0.5)
        self.assertEqual(id1, id2)

    def test_clamps_out_of_range(self):
        # Should not crash with out-of-range linear values
        icon_id = get_color_icon(2.0, -0.5, 0.5)
        self.assertIsInstance(icon_id, int)


if __name__ == "__main__":
    unittest.main()
