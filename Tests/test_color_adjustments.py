# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for the color adjustments math helpers.

Runs inside Blender via::

    blender -b --factory-startup -P Tests/conftest.py --python-exit-code 1
"""

import sys
import unittest
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent
_repo_root = _tests_dir.parent
_addon_root = _repo_root / "HUE"
for p in (_tests_dir, _repo_root, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import numpy as np

from HUE.operators.color_adjustments import (
    _apply_brightness_contrast,
    _apply_hue_saturation,
    _apply_layer_blend,
    _apply_levels,
    _hsv_to_rgb,
    _rgb_to_hsv,
)


class TestApplyLevels(unittest.TestCase):
    """Tests for the _apply_levels helper."""

    def test_identity(self):
        """Default parameters produce no change."""
        rgb = np.array([[0.0, 0.25, 0.5], [0.75, 1.0, 0.1]], dtype=np.float32)
        result = _apply_levels(rgb, 0.0, 1.0, 1.0, 0.0, 1.0)
        np.testing.assert_array_almost_equal(result, rgb, decimal=5)

    def test_invert_via_output(self):
        """Swapping output black/white inverts the value."""
        rgb = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
        result = _apply_levels(rgb, 0.0, 1.0, 1.0, 1.0, 0.0)
        np.testing.assert_array_almost_equal(result, [[1.0, 0.5, 0.0]], decimal=5)

    def test_input_range_clamp(self):
        """Input black/white remaps and clamps the range."""
        rgb = np.array([[0.0, 0.25, 0.5, 0.75, 1.0]], dtype=np.float32)
        result = _apply_levels(rgb, 0.25, 0.75, 1.0, 0.0, 1.0)
        self.assertAlmostEqual(float(result[0, 0]), 0.0, places=4)
        self.assertAlmostEqual(float(result[0, 2]), 0.5, places=4)
        self.assertAlmostEqual(float(result[0, 4]), 1.0, places=4)

    def test_gamma(self):
        """Gamma > 1 lightens midtones."""
        rgb = np.array([[0.25, 0.5, 0.75]], dtype=np.float32)
        result = _apply_levels(rgb, 0.0, 1.0, 2.0, 0.0, 1.0)
        self.assertGreater(float(result[0, 0]), 0.25)
        self.assertGreater(float(result[0, 1]), 0.5)


class TestApplyBrightnessContrast(unittest.TestCase):
    """Tests for _apply_brightness_contrast."""

    def test_identity(self):
        rgb = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
        result = _apply_brightness_contrast(rgb, 0.0, 0.0)
        np.testing.assert_array_almost_equal(result, rgb, decimal=5)

    def test_brightness_offset(self):
        rgb = np.array([[0.5, 0.5, 0.5]], dtype=np.float32)
        result = _apply_brightness_contrast(rgb, 0.1, 0.0)
        np.testing.assert_array_almost_equal(result, [[0.6, 0.6, 0.6]], decimal=5)

    def test_contrast_increases_spread(self):
        rgb = np.array([[0.25, 0.5, 0.75]], dtype=np.float32)
        result = _apply_brightness_contrast(rgb, 0.0, 1.0)
        # Contrast=1 → factor=2, so (x-0.5)*2+0.5
        np.testing.assert_array_almost_equal(result, [[0.0, 0.5, 1.0]], decimal=5)


class TestRgbHsvRoundTrip(unittest.TestCase):
    """Tests for _rgb_to_hsv and _hsv_to_rgb."""

    def test_round_trip(self):
        rgb = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.5, 0.5, 0.5],
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
        ], dtype=np.float32)
        result = _hsv_to_rgb(_rgb_to_hsv(rgb))
        np.testing.assert_array_almost_equal(result, rgb, decimal=5)

    def test_red_hue(self):
        rgb = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        hsv = _rgb_to_hsv(rgb)
        self.assertAlmostEqual(float(hsv[0, 0]), 0.0, places=4)
        self.assertAlmostEqual(float(hsv[0, 1]), 1.0, places=4)
        self.assertAlmostEqual(float(hsv[0, 2]), 1.0, places=4)

    def test_green_hue(self):
        rgb = np.array([[0.0, 1.0, 0.0]], dtype=np.float32)
        hsv = _rgb_to_hsv(rgb)
        self.assertAlmostEqual(float(hsv[0, 0]), 1.0 / 3.0, places=4)

    def test_grey_has_zero_saturation(self):
        rgb = np.array([[0.5, 0.5, 0.5]], dtype=np.float32)
        hsv = _rgb_to_hsv(rgb)
        self.assertAlmostEqual(float(hsv[0, 1]), 0.0, places=4)


class TestApplyHueSaturation(unittest.TestCase):
    """Tests for _apply_hue_saturation."""

    def test_identity(self):
        rgb = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
        result = _apply_hue_saturation(rgb, 0.5, 1.0, 1.0)
        np.testing.assert_array_almost_equal(result, rgb, decimal=4)

    def test_desaturate(self):
        rgb = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        result = _apply_hue_saturation(rgb, 0.5, 0.0, 1.0)
        # Fully desaturated red → grey
        self.assertAlmostEqual(float(result[0, 0]), float(result[0, 1]), places=4)
        self.assertAlmostEqual(float(result[0, 1]), float(result[0, 2]), places=4)

    def test_hue_shift_180(self):
        """Shifting hue by 0.5 (180°) turns red to cyan."""
        rgb = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        result = _apply_hue_saturation(rgb, 1.0, 1.0, 1.0)
        # hue_shift=1.0 → +0.5 from centre → red→cyan
        self.assertAlmostEqual(float(result[0, 0]), 0.0, places=3)
        self.assertGreater(float(result[0, 1]), 0.9)
        self.assertGreater(float(result[0, 2]), 0.9)


class TestApplyLayerBlend(unittest.TestCase):
    """Tests for _apply_layer_blend."""

    def _base_blend(self):
        return np.array([[0.5, 0.5, 0.5], [0.2, 0.4, 0.8]], dtype=np.float32)

    def _blend_layer(self):
        return np.array([[1.0, 1.0, 1.0], [0.5, 0.5, 0.5]], dtype=np.float32)

    def test_mix_full_factor(self):
        """MIX with factor=1 replaces base with blend."""
        result = _apply_layer_blend(self._base_blend(), self._blend_layer(), "MIX", 1.0)
        np.testing.assert_array_almost_equal(result, self._blend_layer(), decimal=5)

    def test_mix_zero_factor(self):
        """MIX with factor=0 leaves base unchanged."""
        base = self._base_blend()
        result = _apply_layer_blend(base.copy(), self._blend_layer(), "MIX", 0.0)
        np.testing.assert_array_almost_equal(result, base, decimal=5)

    def test_mix_half_factor(self):
        """MIX with factor=0.5 averages base and blend."""
        base = self._base_blend()
        blend = self._blend_layer()
        result = _apply_layer_blend(base.copy(), blend, "MIX", 0.5)
        expected = base + (blend - base) * 0.5
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_multiply(self):
        """MULTIPLY blends toward base*blend."""
        base = self._base_blend()
        blend = self._blend_layer()
        result = _apply_layer_blend(base.copy(), blend, "MULTIPLY", 1.0)
        np.testing.assert_array_almost_equal(result, base * blend, decimal=5)

    def test_add(self):
        """ADD adds blend on top."""
        base = self._base_blend()
        blend = self._blend_layer()
        result = _apply_layer_blend(base.copy(), blend, "ADD", 1.0)
        np.testing.assert_array_almost_equal(result, base + blend, decimal=5)

    def test_subtract(self):
        """SUBTRACT removes blend from base."""
        base = self._base_blend()
        blend = self._blend_layer()
        result = _apply_layer_blend(base.copy(), blend, "SUBTRACT", 1.0)
        np.testing.assert_array_almost_equal(result, base - blend, decimal=5)

    def test_screen(self):
        """SCREEN produces 1 - (1-base)(1-blend) at full factor."""
        base = self._base_blend()
        blend = self._blend_layer()
        result = _apply_layer_blend(base.copy(), blend, "SCREEN", 1.0)
        expected = 1.0 - (1.0 - base) * (1.0 - blend)
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_overlay(self):
        """OVERLAY at full factor applies overlay formula."""
        base = self._base_blend()
        blend = self._blend_layer()
        result = _apply_layer_blend(base.copy(), blend, "OVERLAY", 1.0)
        lo = 2.0 * base * blend
        hi = 1.0 - 2.0 * (1.0 - base) * (1.0 - blend)
        expected = np.where(base < 0.5, lo, hi)
        np.testing.assert_array_almost_equal(result, expected, decimal=5)


if __name__ == "__main__":
    unittest.main()
