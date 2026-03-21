# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests for operators/add_color_by_position.py gradient sources.

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

import bpy
import numpy as np

from HUE.operators.add_color_by_position import HUE_OT_add_color_by_position


# ---- Helpers -----------------------------------------------------------------

def _create_mesh_object(name="TestObj", verts=None, faces=None):
    if verts is None:
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    if faces is None:
        faces = [(0, 1, 2, 3)]

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _cleanup():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


# ---- Gradient source tests ---------------------------------------------------

class TestValenceValues(unittest.TestCase):
    def setUp(self):
        _cleanup()
        # Two triangles sharing an edge: v0-v1-v2 and v0-v2-v3
        verts = [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2), (0, 2, 3)]
        self.obj = _create_mesh_object("ValenceTest", verts, faces)

    def test_normalized_range(self):
        values = HUE_OT_add_color_by_position._valence_values(self.obj)
        self.assertEqual(len(values), 4)
        self.assertAlmostEqual(float(values.min()), 0.0, places=5)
        self.assertAlmostEqual(float(values.max()), 1.0, places=5)

    def test_shared_edge_vertex_has_higher_valence(self):
        """Vertices 0 and 2 share both faces, so they should have higher valence."""
        values = HUE_OT_add_color_by_position._valence_values(self.obj)
        # v0 connects to v1, v2, v3 (3 edges), v1 connects to v0, v2 (2 edges)
        self.assertGreater(float(values[0]), float(values[1]))

    def tearDown(self):
        _cleanup()


class TestFaceAreaValues(unittest.TestCase):
    def setUp(self):
        _cleanup()
        # Two quads of different sizes
        verts = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # 1x1 quad
            (1, 0, 0), (3, 0, 0), (3, 2, 0), (1, 2, 0),   # 2x2 quad
        ]
        faces = [(0, 1, 2, 3), (4, 5, 6, 7)]
        self.obj = _create_mesh_object("FaceAreaTest", verts, faces)

    def test_normalized_range(self):
        values = HUE_OT_add_color_by_position._face_area_values(self.obj)
        self.assertEqual(len(values), 8)
        self.assertAlmostEqual(float(values.min()), 0.0, places=5)
        self.assertAlmostEqual(float(values.max()), 1.0, places=5)

    def tearDown(self):
        _cleanup()


class TestEdgeLengthVarianceValues(unittest.TestCase):
    def setUp(self):
        _cleanup()
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2, 3)]
        self.obj = _create_mesh_object("EdgeVarTest", verts, faces)

    def test_finite_values(self):
        """A unit quad should produce finite variance values."""
        values = HUE_OT_add_color_by_position._edge_length_variance_values(self.obj)
        self.assertEqual(len(values), 4)
        self.assertTrue(np.all(np.isfinite(values)))

    def tearDown(self):
        _cleanup()


class TestFaceQualityValues(unittest.TestCase):
    def test_equilateral_uniform(self):
        """Single equilateral triangle — all vertices get the same quality."""
        _cleanup()
        verts = [(0, 0, 0), (1, 0, 0), (0.5, 0.866, 0)]
        faces = [(0, 1, 2)]
        obj = _create_mesh_object("QualityTest", verts, faces)
        values = HUE_OT_add_color_by_position._face_quality_values(obj)
        self.assertEqual(len(values), 3)
        self.assertAlmostEqual(float(values[0]), float(values[1]), places=5)
        _cleanup()

    def test_equilateral_higher_than_degenerate(self):
        """Equilateral triangle scores higher quality than a nearly-flat one."""
        _cleanup()
        verts = [
            (0, 0, 0), (1, 0, 0), (0.5, 0.866, 0),  # equilateral
            (2, 0, 0), (3, 0, 0), (2.5, 0.01, 0),     # very flat
        ]
        faces = [(0, 1, 2), (3, 4, 5)]
        obj = _create_mesh_object("QualityTest2", verts, faces)
        values = HUE_OT_add_color_by_position._face_quality_values(obj)
        self.assertGreater(float(np.mean(values[:3])), float(np.mean(values[3:])))
        _cleanup()


class TestCotangentCurvatureValues(unittest.TestCase):
    def test_sphere_normalized_range(self):
        """UV sphere has varied curvature; result should span [0, 1]."""
        _cleanup()
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4)
        obj = bpy.context.active_object
        values = HUE_OT_add_color_by_position._cotangent_curvature_values(obj)
        self.assertEqual(len(values), len(obj.data.vertices))
        self.assertTrue(np.all(np.isfinite(values)))
        self.assertAlmostEqual(float(values.min()), 0.0, places=5)
        self.assertAlmostEqual(float(values.max()), 1.0, places=5)
        _cleanup()

    def test_sphere_poles_differ_from_equator(self):
        """Poles of a UV sphere have different curvature than the equator."""
        _cleanup()
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4)
        obj = bpy.context.active_object
        values = HUE_OT_add_color_by_position._cotangent_curvature_values(obj)
        unique_vals = np.unique(np.round(values, decimals=3))
        self.assertGreater(len(unique_vals), 1)
        _cleanup()

    def test_flat_grid_finite(self):
        """Flat grid should produce all-finite curvature values."""
        _cleanup()
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4)
        obj = bpy.context.active_object
        values = HUE_OT_add_color_by_position._cotangent_curvature_values(obj)
        self.assertTrue(np.all(np.isfinite(values)))
        _cleanup()

    def test_v_shape_triangle_mesh(self):
        """Two triangles in a V shape — non-flat, 4 vertices."""
        _cleanup()
        verts = [(0, 0, 0), (1, 0, 0), (0.5, 1, 0.5), (0.5, 1, -0.5)]
        faces = [(0, 1, 2), (0, 1, 3)]
        obj = _create_mesh_object("CotTri", verts, faces)
        values = HUE_OT_add_color_by_position._cotangent_curvature_values(obj)
        self.assertEqual(len(values), 4)
        self.assertTrue(np.all(np.isfinite(values)))
        _cleanup()


class TestNormalizePerIsland(unittest.TestCase):
    def test_two_islands_independent_range(self):
        """Two disjoint quads with different value ranges each normalize to 0–1."""
        _cleanup()
        verts = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # island A
            (5, 0, 0), (6, 0, 0), (6, 1, 0), (5, 1, 0),   # island B
        ]
        faces = [(0, 1, 2, 3), (4, 5, 6, 7)]
        obj = _create_mesh_object("IslandTest", verts, faces)
        # Island A values 0.2–0.4, Island B values 0.7–0.9
        values = np.array([0.2, 0.4, 0.3, 0.2, 0.7, 0.9, 0.8, 0.7])
        result = HUE_OT_add_color_by_position._normalize_per_island(obj, values)
        # Each island should span 0–1
        self.assertAlmostEqual(float(result[:4].min()), 0.0, places=5)
        self.assertAlmostEqual(float(result[:4].max()), 1.0, places=5)
        self.assertAlmostEqual(float(result[4:].min()), 0.0, places=5)
        self.assertAlmostEqual(float(result[4:].max()), 1.0, places=5)
        _cleanup()

    def test_single_island_matches_global(self):
        """A single connected mesh island should normalize the same as global."""
        _cleanup()
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2, 3)]
        obj = _create_mesh_object("SingleIsland", verts, faces)
        values = np.array([0.3, 0.7, 0.5, 0.3])
        result = HUE_OT_add_color_by_position._normalize_per_island(obj, values)
        expected = HUE_OT_add_color_by_position._normalize_np(values)
        np.testing.assert_array_almost_equal(result, expected, decimal=5)
        _cleanup()

    def test_uniform_island_becomes_zero(self):
        """An island where all vertices have the same value normalizes to 0."""
        _cleanup()
        verts = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # island A
            (5, 0, 0), (6, 0, 0), (6, 1, 0), (5, 1, 0),   # island B (uniform)
        ]
        faces = [(0, 1, 2, 3), (4, 5, 6, 7)]
        obj = _create_mesh_object("UniformIsland", verts, faces)
        values = np.array([0.2, 0.8, 0.5, 0.2, 0.5, 0.5, 0.5, 0.5])
        result = HUE_OT_add_color_by_position._normalize_per_island(obj, values)
        np.testing.assert_array_almost_equal(result[4:], [0.0, 0.0, 0.0, 0.0], decimal=5)
        _cleanup()

    def test_does_not_modify_original(self):
        """The input array should not be modified in place."""
        _cleanup()
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2, 3)]
        obj = _create_mesh_object("NoMutate", verts, faces)
        values = np.array([0.1, 0.9, 0.5, 0.3])
        original = values.copy()
        HUE_OT_add_color_by_position._normalize_per_island(obj, values)
        np.testing.assert_array_equal(values, original)
        _cleanup()


if __name__ == "__main__":
    unittest.main()
