# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for utilities/color_utilities.py.

Runs inside Blender via::

    blender -b --factory-startup -P Tests/conftest.py --python-exit-code 1
"""

import sys
import unittest
from pathlib import Path

# ---- path bootstrap (when run directly, not via conftest) --------------------
_tests_dir = Path(__file__).resolve().parent
_addon_root = _tests_dir.parent / "HUE"
for p in (_tests_dir, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import bpy
import numpy as np

from utilities.color_utilities import (
    _color_distance,
    apply_mask_array,
    apply_mask_constant,
    build_vertex_loop_map,
    bulk_get_colors,
    bulk_set_colors,
    ensure_object_mode,
    get_active_color_attribute,
    get_color_from_palette,
    get_distinct_random_colors,
    get_masked_color,
    get_random_color,
    get_random_color_by_hue,
    get_random_color_by_RGBA,
    get_selected_color_indices,
)


# ---- Helpers -----------------------------------------------------------------

def _create_mesh_object(name="TestObj", verts=None, faces=None):
    """Create a simple mesh object and link it to the scene."""
    if verts is None:
        # Default: unit quad (4 verts, 1 face, 4 loops)
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    if faces is None:
        faces = [(0, 1, 2, 3)]

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def _cleanup_objects():
    """Remove all objects and meshes created during a test."""
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.active_object else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Purge orphaned meshes
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


# ==============================================================================
# Pure-function tests (no Blender data needed)
# ==============================================================================


class TestRandomColorGenerators(unittest.TestCase):
    """Tests for get_random_color_by_RGBA and get_random_color_by_hue."""

    def test_rgba_returns_4_values_in_range(self):
        for _ in range(50):
            c = get_random_color_by_RGBA()
            self.assertEqual(len(c), 4)
            for v in c:
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_hue_returns_saturated_colors(self):
        """Hue-based colors with S=1 L=0.5 should never be fully grey."""
        for _ in range(50):
            c = get_random_color_by_hue()
            self.assertEqual(len(c), 4)
            r, g, b, _ = c
            self.assertFalse(r == g == b, "Expected saturated color, got grey")


class TestGetRandomColor(unittest.TestCase):
    def test_mode_rgba(self):
        self.assertEqual(len(get_random_color("RGBA")), 4)

    def test_mode_hue(self):
        self.assertEqual(len(get_random_color("Hue")), 4)

    def test_mode_palette(self):
        palette = [(0.1, 0.2, 0.3, 1.0), (0.4, 0.5, 0.6, 1.0)]
        self.assertIn(get_random_color("Palette", palette=palette), palette)

    def test_unknown_mode_returns_none(self):
        self.assertIsNone(get_random_color("UNKNOWN"))


class TestGetMaskedColor(unittest.TestCase):
    def test_full_and_empty_mask(self):
        old = (0.1, 0.2, 0.3, 0.4)
        new = (0.5, 0.6, 0.7, 0.8)
        self.assertEqual(
            get_masked_color(old, new, (True, True, True, True)),
            [0.5, 0.6, 0.7, 0.8],
        )
        self.assertEqual(
            get_masked_color(old, new, (False, False, False, False)),
            [0.1, 0.2, 0.3, 0.4],
        )

    def test_partial_mask(self):
        old = (0.1, 0.2, 0.3, 0.4)
        new = (0.5, 0.6, 0.7, 0.8)
        self.assertEqual(
            get_masked_color(old, new, (True, False, True, False)),
            [0.5, 0.2, 0.7, 0.4],
        )

    def test_does_not_mutate_input(self):
        old = [0.1, 0.2, 0.3, 0.4]
        new = [0.5, 0.6, 0.7, 0.8]
        get_masked_color(old, new)
        self.assertEqual(old, [0.1, 0.2, 0.3, 0.4])


class TestGetColorFromPalette(unittest.TestCase):
    def test_returns_item_from_palette(self):
        palette = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)]
        for _ in range(30):
            self.assertIn(get_color_from_palette(palette), palette)

    def test_single_element(self):
        palette = [(0.5, 0.5, 0.5, 1.0)]
        self.assertEqual(get_color_from_palette(palette), (0.5, 0.5, 0.5, 1.0))


class TestColorDistance(unittest.TestCase):
    def test_same_color_is_zero(self):
        c = (0.5, 0.5, 0.5, 1.0)
        self.assertAlmostEqual(_color_distance(c, c), 0.0)

    def test_black_to_white(self):
        self.assertAlmostEqual(
            _color_distance((0, 0, 0, 1), (1, 1, 1, 1)), 3**0.5
        )

    def test_single_channel_diff(self):
        self.assertAlmostEqual(
            _color_distance((0, 0, 0, 1), (1, 0, 0, 1)), 1.0
        )

    def test_ignores_alpha(self):
        self.assertAlmostEqual(
            _color_distance((0.5, 0.5, 0.5, 0.0), (0.5, 0.5, 0.5, 1.0)), 0.0
        )


class TestGetDistinctRandomColors(unittest.TestCase):
    def test_returns_correct_count(self):
        self.assertEqual(len(get_distinct_random_colors(5)), 5)

    def test_single_color(self):
        colors = get_distinct_random_colors(1)
        self.assertEqual(len(colors), 1)
        self.assertEqual(len(colors[0]), 4)

    def test_colors_are_not_identical(self):
        colors = get_distinct_random_colors(3, min_distance=0.3)
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                self.assertNotEqual(colors[i], colors[j])

    def test_palette_mode(self):
        palette = [
            (1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1),
            (1, 1, 0, 1), (1, 0, 1, 1), (0, 1, 1, 1),
        ]
        colors = get_distinct_random_colors(3, mode="Palette", palette=palette)
        self.assertEqual(len(colors), 3)
        for c in colors:
            self.assertIn(c, palette)


# ---- Numpy mask helpers (pure, no bpy) ---------------------------------------

class TestApplyMaskConstant(unittest.TestCase):
    def test_all_channels_no_indices(self):
        colors = np.zeros((4, 4), dtype=np.float32)
        apply_mask_constant(colors, (1.0, 0.5, 0.25, 0.75),
                            (True, True, True, True))
        expected = np.array([[1.0, 0.5, 0.25, 0.75]] * 4, dtype=np.float32)
        np.testing.assert_array_almost_equal(colors, expected)

    def test_partial_mask_no_indices(self):
        colors = np.ones((3, 4), dtype=np.float32)
        apply_mask_constant(colors, (0.0, 0.0, 0.0, 0.0),
                            (True, False, True, False))
        self.assertAlmostEqual(colors[0, 0], 0.0)
        self.assertAlmostEqual(colors[0, 1], 1.0)
        self.assertAlmostEqual(colors[0, 2], 0.0)
        self.assertAlmostEqual(colors[0, 3], 1.0)

    def test_with_indices(self):
        colors = np.zeros((5, 4), dtype=np.float32)
        idx = np.array([1, 3], dtype=np.intp)
        apply_mask_constant(colors, (1, 1, 1, 1), (True, True, True, True),
                            indices=idx)
        np.testing.assert_array_almost_equal(colors[0], [0, 0, 0, 0])
        np.testing.assert_array_almost_equal(colors[1], [1, 1, 1, 1])
        np.testing.assert_array_almost_equal(colors[2], [0, 0, 0, 0])
        np.testing.assert_array_almost_equal(colors[3], [1, 1, 1, 1])
        np.testing.assert_array_almost_equal(colors[4], [0, 0, 0, 0])

    def test_empty_indices(self):
        colors = np.ones((3, 4), dtype=np.float32)
        idx = np.array([], dtype=np.intp)
        apply_mask_constant(colors, (0, 0, 0, 0), (True, True, True, True),
                            indices=idx)
        np.testing.assert_array_almost_equal(colors, np.ones((3, 4)))


class TestApplyMaskArray(unittest.TestCase):
    def test_all_channels_no_indices(self):
        colors = np.zeros((3, 4), dtype=np.float32)
        new_colors = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 0.0, 0.1],
        ], dtype=np.float32)
        apply_mask_array(colors, new_colors, (True, True, True, True))
        np.testing.assert_array_almost_equal(colors, new_colors)

    def test_partial_mask_no_indices(self):
        colors = np.ones((2, 4), dtype=np.float32)
        new_colors = np.zeros((2, 4), dtype=np.float32)
        apply_mask_array(colors, new_colors, (False, True, False, True))
        self.assertAlmostEqual(colors[0, 0], 1.0)
        self.assertAlmostEqual(colors[0, 1], 0.0)
        self.assertAlmostEqual(colors[0, 2], 1.0)
        self.assertAlmostEqual(colors[0, 3], 0.0)

    def test_with_indices(self):
        colors = np.zeros((4, 4), dtype=np.float32)
        idx = np.array([0, 2], dtype=np.intp)
        new_colors = np.array([
            [1.0, 1.0, 1.0, 1.0],
            [0.5, 0.5, 0.5, 0.5],
        ], dtype=np.float32)
        apply_mask_array(colors, new_colors, (True, True, True, True),
                         indices=idx)
        np.testing.assert_array_almost_equal(colors[0], [1, 1, 1, 1])
        np.testing.assert_array_almost_equal(colors[1], [0, 0, 0, 0])
        np.testing.assert_array_almost_equal(colors[2], [0.5, 0.5, 0.5, 0.5])
        np.testing.assert_array_almost_equal(colors[3], [0, 0, 0, 0])


# ==============================================================================
# Integration tests (real Blender data)
# ==============================================================================


class TestBuildVertexLoopMap(unittest.TestCase):
    def setUp(self):
        _cleanup_objects()

    def tearDown(self):
        _cleanup_objects()

    def test_quad_has_4_loops(self):
        obj = _create_mesh_object()
        vmap = build_vertex_loop_map(obj)
        # A single quad: 4 verts, each used by exactly 1 loop
        self.assertEqual(len(vmap), 4)
        for loops in vmap.values():
            self.assertEqual(len(loops), 1)

    def test_shared_vertex_multiple_loops(self):
        """Two triangles sharing an edge → shared verts appear in 2 loops."""
        verts = [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (1.5, 1, 0)]
        faces = [(0, 1, 2), (1, 3, 2)]
        obj = _create_mesh_object(verts=verts, faces=faces)
        vmap = build_vertex_loop_map(obj)
        # Verts 1 and 2 are shared by both faces → 2 loops each
        self.assertEqual(len(vmap[1]), 2)
        self.assertEqual(len(vmap[2]), 2)
        # Verts 0 and 3 are in one face each → 1 loop each
        self.assertEqual(len(vmap[0]), 1)
        self.assertEqual(len(vmap[3]), 1)


class TestGetActiveColorAttribute(unittest.TestCase):
    def setUp(self):
        _cleanup_objects()

    def tearDown(self):
        _cleanup_objects()

    def test_creates_attribute_if_missing(self):
        obj = _create_mesh_object()
        self.assertEqual(len(obj.data.color_attributes), 0)
        attr = get_active_color_attribute(obj)
        self.assertIsNotNone(attr)
        self.assertEqual(len(obj.data.color_attributes), 1)
        self.assertEqual(attr.name, "Color")

    def test_returns_existing_attribute(self):
        obj = _create_mesh_object()
        obj.data.color_attributes.new(name="MyCol", type="FLOAT_COLOR",
                                      domain="CORNER")
        attr = get_active_color_attribute(obj)
        self.assertIsNotNone(attr)
        # Should not have created a second one
        self.assertEqual(len(obj.data.color_attributes), 1)


class TestBulkGetSetColors(unittest.TestCase):
    def setUp(self):
        _cleanup_objects()

    def tearDown(self):
        _cleanup_objects()

    def test_round_trip_corner_domain(self):
        """Write colors, read them back, verify they match."""
        obj = _create_mesh_object()
        attr = obj.data.color_attributes.new(
            name="TestCol", type="FLOAT_COLOR", domain="CORNER"
        )
        n = len(attr.data)  # 4 loops for a quad
        self.assertEqual(n, 4)

        # Write solid red
        red = np.array([[1.0, 0.0, 0.0, 1.0]] * n, dtype=np.float32)
        bulk_set_colors(attr, red)
        obj.data.update()

        # Read back — sRGB round-trip has ~1e-5 precision loss
        result = bulk_get_colors(attr)
        np.testing.assert_array_almost_equal(result, red, decimal=3)

    def test_round_trip_point_domain(self):
        obj = _create_mesh_object()
        attr = obj.data.color_attributes.new(
            name="TestColPt", type="FLOAT_COLOR", domain="POINT"
        )
        n = len(attr.data)  # 4 verts
        self.assertEqual(n, 4)

        colors = np.random.rand(n, 4).astype(np.float32)
        bulk_set_colors(attr, colors)
        obj.data.update()

        result = bulk_get_colors(attr)
        np.testing.assert_array_almost_equal(result, colors, decimal=3)

    def test_per_element_values(self):
        """Each loop gets a distinct color."""
        obj = _create_mesh_object()
        attr = obj.data.color_attributes.new(
            name="Distinct", type="FLOAT_COLOR", domain="CORNER"
        )
        n = len(attr.data)
        colors = np.zeros((n, 4), dtype=np.float32)
        for i in range(n):
            colors[i] = [i / n, 0.0, 0.0, 1.0]
        bulk_set_colors(attr, colors)
        obj.data.update()

        result = bulk_get_colors(attr)
        np.testing.assert_array_almost_equal(result, colors, decimal=3)


class TestEnsureObjectMode(unittest.TestCase):
    def setUp(self):
        _cleanup_objects()

    def tearDown(self):
        _cleanup_objects()

    def test_stays_in_object_mode(self):
        obj = _create_mesh_object()
        self.assertEqual(obj.mode, "OBJECT")
        with ensure_object_mode(obj):
            self.assertEqual(obj.mode, "OBJECT")
        self.assertEqual(obj.mode, "OBJECT")

    def test_restores_edit_mode(self):
        obj = _create_mesh_object()
        bpy.ops.object.mode_set(mode="EDIT")
        self.assertEqual(obj.mode, "EDIT")

        with ensure_object_mode(obj):
            self.assertEqual(obj.mode, "OBJECT")

        self.assertEqual(obj.mode, "EDIT")
        bpy.ops.object.mode_set(mode="OBJECT")


class TestGetSelectedColorIndices(unittest.TestCase):
    def setUp(self):
        _cleanup_objects()

    def tearDown(self):
        _cleanup_objects()

    def test_none_select_mode_returns_none(self):
        obj = _create_mesh_object()
        result = get_selected_color_indices(obj, None, "CORNER")
        self.assertIsNone(result)

    def test_point_domain_vertex_select(self):
        """Select one vertex in POINT domain → get that vertex index."""
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2, 3)]
        obj = _create_mesh_object(verts=verts, faces=faces)

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")

        # Select vertex 0 only
        obj.data.vertices[0].select = True
        obj.data.vertices[1].select = False
        obj.data.vertices[2].select = False
        obj.data.vertices[3].select = False

        select_mode = (True, False, False)  # vertex mode
        indices = get_selected_color_indices(obj, select_mode, "POINT")
        np.testing.assert_array_equal(indices, [0])

    def test_corner_domain_face_select(self):
        """Select a face → loops of that face returned."""
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                 (2, 0, 0), (2, 1, 0)]
        faces = [(0, 1, 2, 3), (1, 4, 5, 2)]
        obj = _create_mesh_object(verts=verts, faces=faces)

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")

        # Select only face 0
        obj.data.polygons[0].select = True
        obj.data.polygons[1].select = False

        select_mode = (False, False, True)  # face mode
        indices = get_selected_color_indices(obj, select_mode, "CORNER")

        # Face 0 should have 4 loop indices
        self.assertEqual(len(indices), 4)
        expected_loops = list(obj.data.polygons[0].loop_indices)
        self.assertEqual(sorted(indices.tolist()), sorted(expected_loops))

    def test_corner_domain_nothing_selected(self):
        """No selection → empty array."""
        obj = _create_mesh_object()
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")

        select_mode = (True, False, False)
        indices = get_selected_color_indices(obj, select_mode, "CORNER")
        self.assertEqual(len(indices), 0)


# ==============================================================================

if __name__ == "__main__":
    unittest.main()
