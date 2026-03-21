# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for attribute transfer helpers.

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

from HUE.operators.attribute_transfer import (
    _nearest_vertex_transfer,
    _sample_face_color,
)


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


# ---- Tests -------------------------------------------------------------------

class TestNearestVertexTransfer(unittest.TestCase):
    """Tests for _nearest_vertex_transfer."""

    def test_identity_mapping(self):
        """When source and target positions are identical, colors transfer exactly."""
        positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        colors = np.array([
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
        ], dtype=np.float32)
        result = _nearest_vertex_transfer(positions, positions, colors)
        np.testing.assert_array_almost_equal(result, colors, decimal=5)

    def test_nearest_selection(self):
        """Target vertex picks the closest source vertex color."""
        src_positions = np.array([[0, 0, 0], [10, 0, 0]], dtype=np.float64)
        src_colors = np.array([
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
        ], dtype=np.float32)
        # Target close to first source
        tgt_positions = np.array([[0.1, 0, 0]], dtype=np.float64)
        result = _nearest_vertex_transfer(tgt_positions, src_positions, src_colors)
        np.testing.assert_array_almost_equal(result[0], [1.0, 0.0, 0.0, 1.0], decimal=5)

    def test_output_shape(self):
        src_pos = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        src_colors = np.array([[1, 0, 0, 1], [0, 1, 0, 1]], dtype=np.float32)
        tgt_pos = np.array([[0, 0, 0], [1, 0, 0], [0.5, 0, 0]], dtype=np.float64)
        result = _nearest_vertex_transfer(tgt_pos, src_pos, src_colors)
        self.assertEqual(result.shape, (3, 4))


class TestSampleFaceColor(unittest.TestCase):
    """Tests for _sample_face_color barycentric interpolation."""

    def setUp(self):
        _cleanup()
        # Triangle with known vertex colors (POINT domain)
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        faces = [(0, 1, 2)]
        self.obj = _create_mesh_object("BaryTest", verts, faces)
        # Add POINT domain color attribute
        attr = self.obj.data.color_attributes.new(
            name="TestColors", type="FLOAT_COLOR", domain="POINT"
        )
        # Red, Green, Blue at each vertex
        attr.data[0].color_srgb = (1, 0, 0, 1)
        attr.data[1].color_srgb = (0, 1, 0, 1)
        attr.data[2].color_srgb = (0, 0, 1, 1)

        n = len(attr.data)
        self.src_colors = np.empty((n, 4), dtype=np.float32)
        for i in range(n):
            self.src_colors[i] = attr.data[i].color_srgb

    def test_at_vertex(self):
        """Sampling at a vertex position returns that vertex's color."""
        from mathutils import Vector
        result = _sample_face_color(
            self.obj, self.obj.data.color_attributes["TestColors"],
            self.src_colors, 0, Vector((0, 0, 0)),
        )
        self.assertAlmostEqual(float(result[0]), 1.0, places=3)
        self.assertAlmostEqual(float(result[1]), 0.0, places=3)

    def test_at_centroid(self):
        """Sampling at the centroid blends all three colors equally."""
        from mathutils import Vector
        result = _sample_face_color(
            self.obj, self.obj.data.color_attributes["TestColors"],
            self.src_colors, 0, Vector((1 / 3, 1 / 3, 0)),
        )
        # Each channel ≈ 1/3
        self.assertAlmostEqual(float(result[0]), 1 / 3, places=2)
        self.assertAlmostEqual(float(result[1]), 1 / 3, places=2)
        self.assertAlmostEqual(float(result[2]), 1 / 3, places=2)

    def tearDown(self):
        _cleanup()


if __name__ == "__main__":
    unittest.main()
