# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy.utils.previews
from bpy.types import Panel

from ..base_panel_info import BasePanelInfo

_preset_previews = {}

_SWATCH_COLS = 8
_SWATCH_SIZE = 32
_INDICATOR_SIZE = 8


def _linear_to_srgb(c):
    """Convert a single linear-space float to sRGB."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def _build_swatch_pixels(r, g, b, selected=False):
    """Build RGBA float pixel data for a swatch icon, in-memory."""
    size = _SWATCH_SIZE
    rs, gs, bs = _linear_to_srgb(r), _linear_to_srgb(g), _linear_to_srgb(b)
    ri, gi, bi = int(rs * 255), int(gs * 255), int(bs * 255)

    # Indicator contrast colors based on swatch luminance.
    lum = 0.299 * ri + 0.587 * gi + 0.114 * bi
    fill = (0.16, 0.16, 0.16, 1.0) if lum > 140 else (1.0, 1.0, 1.0, 1.0)
    edge = (0.78, 0.78, 0.78, 1.0) if lum > 140 else (0.31, 0.31, 0.31, 1.0)
    base = (rs, gs, bs, 1.0)

    threshold = 2 * size - _INDICATOR_SIZE - 1
    pixels = []
    for y in range(size):
        for x in range(size):
            if selected:
                s = x + y
                if s == threshold:
                    pixels.extend(edge)
                elif s > threshold:
                    pixels.extend(fill)
                else:
                    pixels.extend(base)
            else:
                pixels.extend(base)
    return pixels


def _get_color_icon(r, g, b, selected=False):
    """Get or create a colored swatch icon, fully in-memory."""
    if "main" not in _preset_previews:
        _preset_previews["main"] = bpy.utils.previews.new()
    pcoll = _preset_previews["main"]

    rs = max(0.0, min(1.0, _linear_to_srgb(r)))
    gs = max(0.0, min(1.0, _linear_to_srgb(g)))
    bs = max(0.0, min(1.0, _linear_to_srgb(b)))
    ri, gi, bi = int(rs * 255), int(gs * 255), int(bs * 255)
    suffix = "_sel" if selected else ""
    key = f"mc_{ri:03d}_{gi:03d}_{bi:03d}{suffix}"

    if key not in pcoll:
        icon = pcoll.new(key)
        icon.icon_size = (_SWATCH_SIZE, _SWATCH_SIZE)
        icon.icon_pixels_float = _build_swatch_pixels(r, g, b, selected)

    return pcoll[key].icon_id


def cleanup_preset_previews():
    """Remove preview collections. Called from ui unregister."""
    for pcoll in _preset_previews.values():
        bpy.utils.previews.remove(pcoll)
    _preset_previews.clear()


class MC_PT_simple_fill_tool_panel(BasePanelInfo, Panel):
    bl_label = "Simple Fill"
    bl_idname = "MC_PT_simple_fill_tool_panel"
    bl_parent_id = "MC_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        simple_fill_tool = context.scene.more_colors_simple_fill_tool

        # --- Active color + apply button ---
        box = layout.box()
        box.label(text="Active Color", icon="BRUSH_DATA")
        row = box.row(align=True)
        row.prop(simple_fill_tool, "selected_color", text="")
        row.operator("morecolors.simple_fill", icon="CHECKMARK")

        layout.separator()

        # --- Color presets (custom swatch grid) ---
        box = layout.box()
        box.label(text="Color Presets", icon="COLOR")
        palette = simple_fill_tool.preset_palette
        if palette and len(palette.colors) > 0:
            active_idx = simple_fill_tool.active_preset_index
            for i, pc in enumerate(palette.colors):
                if i % _SWATCH_COLS == 0:
                    row = box.row(align=True)
                    row.alignment = 'LEFT'
                icon_id = _get_color_icon(*pc.color, selected=(i == active_idx))
                op = row.operator(
                    "morecolors.use_preset_color",
                    text="",
                    icon_value=icon_id,
                )
                op.index = i
        row = box.row(align=True)
        row.operator("morecolors.add_preset_color", icon="ADD", text="")
        if palette and len(palette.colors) > 0:
            row.operator("morecolors.remove_preset_color", icon="REMOVE", text="")
