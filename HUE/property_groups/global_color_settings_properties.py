# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import BoolProperty
from bpy.types import PropertyGroup


class GlobalColorSettingsProperties(PropertyGroup):
    global_color_mask_r: BoolProperty(name="R", description="Use Red Channel", default=True)
    global_color_mask_g: BoolProperty(name="G", description="Use Green Channel", default=True)
    global_color_mask_b: BoolProperty(name="B", description="Use Blue Channel", default=True)
    global_color_mask_a: BoolProperty(name="A", description="Use Alpha Channel", default=True)

    def get_mask(self):
        return (self.global_color_mask_r, self.global_color_mask_g, self.global_color_mask_b, self.global_color_mask_a)
