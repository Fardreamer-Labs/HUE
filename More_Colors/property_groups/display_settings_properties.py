# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, StringProperty
from bpy.types import PropertyGroup


def on_settings_update(self, context):
    if hasattr(context, 'space_data') and context.space_data and hasattr(context.space_data, 'shading'):
        from ..operators.display_vertex_colors import update_display
        update_display(context)


class DisplaySettingsProperties(PropertyGroup):
    previous_shading_type: StringProperty(name="Previous Shading Type", default="SOLID")
    previous_color_type: StringProperty(name="Previous Color Type", default="OBJECT")
    previous_light_type: StringProperty(name="Previous Light Type", default="STUDIO")

    display_mode: EnumProperty(
        name="Vertex Colors Display Mode",
        description="Determines how vertex colors will be presented",
        items=[
            ("Off", "Off", "Do not show vertex color."),
            ("RGB", "RGB", "Show only RGB components of vertex colors."),
            ("Alpha", "Alpha", "Show only alpha component of vertex colors."),
        ],
        default="Off",
        update=on_settings_update,
    )

    alpha_display_material_name: StringProperty(
        name="Alpha Display Material Name",
        default="MORECOLORS_VertexColorAlphaDisplay",
    )
