# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests for operators/symmetrize_vertex_colors.py.

Runs inside Blender via::

    blender -b --factory-startup -P Tests/conftest.py --python-exit-code 1
"""

import sys
import unittest
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent
_repo_root = _tests_dir.parent
_addon_root = _repo_root / "More_Colors"
for p in (_tests_dir, _repo_root, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import bpy
import numpy as np

from More_Colors.operators.symmetrize_vertex_colors import MC_OT_symmetrize_vertex_colors
from More_Colors.utilities.color_utilities import (
    bulk_get_colors, bulk_set_colors, get_active_color_attribute,
)


# ---- Helpers -----------------------------------------------------------------

def _create_symmetric_mesh(name="SymObj"):
    """Create a mesh with 4 verts symmetric across X: (-1,0,0), (1,0,0), (-1,1,0), (1,1,0)."""
    verts = [(-1, 0, 0), (1, 0, 0), (-1, 1, 0), (1, 1, 0)]
    faces = [(0, 1, 3, 2)]

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Create a POINT domain color attribute for simpler testing
    mesh.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
    mesh.color_attributes.active_color = mesh.color_attributes["Color"]

    return obj


def _cleanup():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)


# ---- Tests -------------------------------------------------------------------

class TestSymmetrizeVertexColors(unittest.TestCase):

    def setUp(self):
        _cleanup()
        self.obj = _create_symmetric_mesh()
        self.mask = (True, True, True, True)

    def tearDown(self):
        _cleanup()

    def test_positive_to_negative_x(self):
        """Colors on +X verts (indices 1,3) should be copied to -X verts (indices 0,2)."""
        ca = get_active_color_attribute(self.obj)
        colors = bulk_get_colors(ca)
        # Set +X verts to red
        colors[1] = [1, 0, 0, 1]  # vert at (1,0,0)
        colors[3] = [0, 1, 0, 1]  # vert at (1,1,0)
        # Set -X verts to blue
        colors[0] = [0, 0, 1, 1]  # vert at (-1,0,0)
        colors[2] = [0, 0, 1, 1]  # vert at (-1,1,0)
        bulk_set_colors(ca, colors)

        MC_OT_symmetrize_vertex_colors._symmetrize_object(
            self.obj, axis_index=0, direction="POSITIVE_TO_NEGATIVE",
            threshold=0.001, mask=self.mask, select_mode=None,
        )

        result = bulk_get_colors(ca)
        # -X verts should now match their +X mirrors
        np.testing.assert_array_almost_equal(result[0], [1, 0, 0, 1], decimal=4)
        np.testing.assert_array_almost_equal(result[2], [0, 1, 0, 1], decimal=4)
        # +X verts should remain unchanged
        np.testing.assert_array_almost_equal(result[1], [1, 0, 0, 1], decimal=4)
        np.testing.assert_array_almost_equal(result[3], [0, 1, 0, 1], decimal=4)

    def test_negative_to_positive_x(self):
        """Colors on -X verts should be copied to +X verts."""
        ca = get_active_color_attribute(self.obj)
        colors = bulk_get_colors(ca)
        colors[0] = [1, 1, 0, 1]  # -X vert
        colors[2] = [0, 1, 1, 1]  # -X vert
        colors[1] = [0, 0, 0, 1]  # +X vert
        colors[3] = [0, 0, 0, 1]  # +X vert
        bulk_set_colors(ca, colors)

        MC_OT_symmetrize_vertex_colors._symmetrize_object(
            self.obj, axis_index=0, direction="NEGATIVE_TO_POSITIVE",
            threshold=0.001, mask=self.mask, select_mode=None,
        )

        result = bulk_get_colors(ca)
        np.testing.assert_array_almost_equal(result[1], [1, 1, 0, 1], decimal=4)
        np.testing.assert_array_almost_equal(result[3], [0, 1, 1, 1], decimal=4)

    def test_no_match_beyond_threshold(self):
        """Verts without a mirror match within threshold should keep original color."""
        # Move vert 0 so it's no longer a mirror of vert 1
        self.obj.data.vertices[0].co.x = -5.0
        self.obj.data.update()

        ca = get_active_color_attribute(self.obj)
        colors = bulk_get_colors(ca)
        colors[0] = [0, 0, 1, 1]
        colors[1] = [1, 0, 0, 1]
        bulk_set_colors(ca, colors)

        MC_OT_symmetrize_vertex_colors._symmetrize_object(
            self.obj, axis_index=0, direction="POSITIVE_TO_NEGATIVE",
            threshold=0.001, mask=self.mask, select_mode=None,
        )

        result = bulk_get_colors(ca)
        # Vert 0 should keep its original color (no mirror within threshold)
        np.testing.assert_array_almost_equal(result[0], [0, 0, 1, 1], decimal=4)

    def test_y_axis_symmetry(self):
        """Symmetrize across Y axis."""
        # Create mesh symmetric in Y
        _cleanup()
        verts = [(0, -1, 0), (0, 1, 0), (1, -1, 0), (1, 1, 0)]
        faces = [(0, 1, 3, 2)]
        mesh = bpy.data.meshes.new("YSymMesh")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new("YSymObj", mesh)
        bpy.context.collection.objects.link(obj)
        mesh.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
        mesh.color_attributes.active_color = mesh.color_attributes["Color"]

        ca = get_active_color_attribute(obj)
        colors = bulk_get_colors(ca)
        colors[1] = [1, 0, 0, 1]  # +Y
        colors[3] = [0, 1, 0, 1]  # +Y
        colors[0] = [0, 0, 0, 1]  # -Y
        colors[2] = [0, 0, 0, 1]  # -Y
        bulk_set_colors(ca, colors)

        MC_OT_symmetrize_vertex_colors._symmetrize_object(
            obj, axis_index=1, direction="POSITIVE_TO_NEGATIVE",
            threshold=0.001, mask=self.mask, select_mode=None,
        )

        result = bulk_get_colors(ca)
        np.testing.assert_array_almost_equal(result[0], [1, 0, 0, 1], decimal=4)
        np.testing.assert_array_almost_equal(result[2], [0, 1, 0, 1], decimal=4)

    def test_center_vertex_unchanged(self):
        """A vertex exactly on the axis (x=0) should not be modified."""
        _cleanup()
        verts = [(-1, 0, 0), (0, 0, 0), (1, 0, 0)]
        faces = [(0, 1, 2)]
        mesh = bpy.data.meshes.new("CenterMesh")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new("CenterObj", mesh)
        bpy.context.collection.objects.link(obj)
        mesh.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
        mesh.color_attributes.active_color = mesh.color_attributes["Color"]

        ca = get_active_color_attribute(obj)
        colors = bulk_get_colors(ca)
        colors[0] = [0, 0, 1, 1]  # -X
        colors[1] = [0.5, 0.5, 0.5, 1]  # center
        colors[2] = [1, 0, 0, 1]  # +X
        bulk_set_colors(ca, colors)

        MC_OT_symmetrize_vertex_colors._symmetrize_object(
            obj, axis_index=0, direction="POSITIVE_TO_NEGATIVE",
            threshold=0.001, mask=self.mask, select_mode=None,
        )

        result = bulk_get_colors(ca)
        # Center vert is on +X side (>=0), so it's a source — should remain unchanged
        np.testing.assert_array_almost_equal(result[1], [0.5, 0.5, 0.5, 1], decimal=4)
        # -X vert should get the +X color
        np.testing.assert_array_almost_equal(result[0], [1, 0, 0, 1], decimal=4)
