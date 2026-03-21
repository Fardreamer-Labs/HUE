# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests for operators/smooth_vertex_colors.py constraint modes.

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

from More_Colors.operators.smooth_vertex_colors import MC_OT_smooth_vertex_colors
from More_Colors.utilities.color_utilities import bulk_get_colors, get_active_color_attribute


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


# ---- Smooth constraint tests -------------------------------------------------

class TestSmoothConstraintFiltering(unittest.TestCase):
    """Test that constraint modes filter edges correctly."""

    def setUp(self):
        _cleanup()
        # Two quads sharing an edge (v1-v2)
        verts = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
            (2, 0, 0), (2, 1, 0),
        ]
        faces = [(0, 1, 2, 3), (1, 4, 5, 2)]
        self.obj = _create_mesh_object("SmoothTest", verts, faces)
        # Ensure a color attribute exists
        get_active_color_attribute(self.obj)

    def test_smooth_none_runs(self):
        """Smooth with NONE constraint should complete without error."""
        mask = (True, True, True, True)
        MC_OT_smooth_vertex_colors._smooth_object(self.obj, 1, 0.5, mask, "NONE")

    def test_smooth_sharp_runs(self):
        """Smooth with SHARP constraint should complete without error."""
        mask = (True, True, True, True)
        MC_OT_smooth_vertex_colors._smooth_object(self.obj, 1, 0.5, mask, "SHARP")

    def test_smooth_seam_runs(self):
        mask = (True, True, True, True)
        MC_OT_smooth_vertex_colors._smooth_object(self.obj, 1, 0.5, mask, "SEAM")

    def test_smooth_boundary_runs(self):
        mask = (True, True, True, True)
        MC_OT_smooth_vertex_colors._smooth_object(self.obj, 1, 0.5, mask, "BOUNDARY")

    def test_sharp_edge_affects_smoothing(self):
        """SHARP constraint should produce different results from NONE on a chain mesh."""
        _cleanup()
        # 4-vertex chain: v0--v1--v2--v3 ; mark v1-v2 sharp
        verts = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]
        edges = [(0, 1), (1, 2), (2, 3)]
        mesh = bpy.data.meshes.new("ChainMesh")
        mesh.from_pydata(verts, edges, [])
        mesh.update()
        obj = bpy.data.objects.new("Chain", mesh)
        bpy.context.collection.objects.link(obj)

        # POINT domain color attribute
        ca = mesh.color_attributes.new("Color", "FLOAT_COLOR", "POINT")
        mesh.color_attributes.active_color = ca

        # Paint black–black–white–white
        def _set_colors():
            ca.data[0].color_srgb = (0, 0, 0, 1)
            ca.data[1].color_srgb = (0, 0, 0, 1)
            ca.data[2].color_srgb = (1, 1, 1, 1)
            ca.data[3].color_srgb = (1, 1, 1, 1)

        # Mark middle edge sharp
        for edge in mesh.edges:
            if set(edge.vertices) == {1, 2}:
                edge.use_edge_sharp = True

        mask = (True, True, True, True)

        _set_colors()
        MC_OT_smooth_vertex_colors._smooth_object(obj, 3, 1.0, mask, "SHARP")
        sharp_result = bulk_get_colors(ca).copy()

        _set_colors()
        MC_OT_smooth_vertex_colors._smooth_object(obj, 3, 1.0, mask, "NONE")
        none_result = bulk_get_colors(ca)

        self.assertFalse(
            np.allclose(sharp_result, none_result, atol=1e-4),
            "SHARP and NONE constraints should produce different smoothing results",
        )

    def tearDown(self):
        _cleanup()


if __name__ == "__main__":
    unittest.main()
