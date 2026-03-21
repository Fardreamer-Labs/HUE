# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Object, PropertyGroup


def _mesh_poll(self, obj):
    return obj.type == "MESH"


class AttributeTransferToolProperties(PropertyGroup):
    source_object: PointerProperty(
        name="Source",
        description="Object to transfer vertex colors from",
        type=Object,
        poll=_mesh_poll,
    )

    transfer_mode: EnumProperty(
        name="Mode",
        description="How to map source vertices to target vertices",
        items=[
            ("NEAREST_VERTEX", "Nearest Vertex",
             "Copy color from the closest vertex on the source mesh", "VERTEXSEL", 1),
            ("NEAREST_SURFACE", "Nearest Surface",
             "Sample color from the closest point on the source surface", "FACESEL", 2),
            ("RAYCAST", "Raycast",
             "Project target normals onto the source surface to sample color", "LIGHT_SPOT", 3),
        ],
        default="NEAREST_VERTEX",
    )

    source_layer: StringProperty(
        name="Layer",
        description="Color attribute layer to read from on the source object (empty = active)",
        default="",
    )

    mix_factor: FloatProperty(
        name="Factor",
        description="Blend factor between existing color and transferred color",
        default=1.0,
        min=0.0,
        max=1.0,
    )
