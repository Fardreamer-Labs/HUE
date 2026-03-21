# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np

from .base_operators import BaseColorOperator
from ..utilities.color_utilities import (
    apply_mask_array, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute, get_selected_color_indices,
)


class MC_OT_color_adjustments(BaseColorOperator):
    """Applies color adjustments (levels, brightness, hue, invert, posterize, layer blend)"""

    bl_label = "Apply Adjustment"
    bl_idname = "morecolors.color_adjustments"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool = context.scene.more_colors_color_adjustments_tool
        mask = context.scene.more_colors_global_color_settings.get_mask()
        select_mode = context.tool_settings.mesh_select_mode if context.mode == 'EDIT_MESH' else None

        if tool.operation == "BLEND" and not tool.blend_layer:
            self.report({"ERROR"}, "No blend layer selected.")
            return {"CANCELLED"}

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                if not self._adjust(obj, tool, mask, select_mode):
                    self.report({"ERROR"}, f"Blend layer '{tool.blend_layer}' not found on {obj.name}.")
                    return {"CANCELLED"}

        self.report({"INFO"}, "Color adjustment applied!")
        return {"FINISHED"}

    @staticmethod
    def _adjust(obj, tool, mask, select_mode):
        color_attribute = get_active_color_attribute(obj)
        indices = get_selected_color_indices(obj, select_mode, color_attribute.domain)
        colors = bulk_get_colors(color_attribute)

        target = np.arange(len(colors), dtype=np.intp) if indices is None else indices
        src = colors[target].copy()

        match tool.operation:
            case "LEVELS":
                src[:, :3] = _apply_levels(
                    src[:, :3],
                    tool.levels_input_black, tool.levels_input_white,
                    tool.levels_gamma,
                    tool.levels_output_black, tool.levels_output_white,
                )
            case "BRIGHTNESS_CONTRAST":
                src[:, :3] = _apply_brightness_contrast(
                    src[:, :3], tool.brightness, tool.contrast,
                )
            case "HUE_SATURATION":
                src[:, :3] = _apply_hue_saturation(
                    src[:, :3], tool.hue_shift, tool.saturation, tool.value_adjust,
                )
            case "INVERT":
                src[:, :3] = 1.0 - src[:, :3]
            case "POSTERIZE":
                levels = max(tool.posterize_levels, 2)
                src[:, :3] = np.round(src[:, :3] * (levels - 1)) / (levels - 1)
            case "BLEND":
                blend_attr = obj.data.color_attributes.get(tool.blend_layer)
                if blend_attr is None:
                    return False
                blend_colors = bulk_get_colors(blend_attr)
                blend_src = blend_colors[target]
                src[:, :3] = _apply_layer_blend(
                    src[:, :3], blend_src[:, :3],
                    tool.blend_mode, tool.blend_factor,
                )

        src[:, :3] = np.clip(src[:, :3], 0.0, 1.0)
        apply_mask_array(colors, src, mask, target)
        bulk_set_colors(color_attribute, colors)
        obj.data.update()
        return True


# ---------------------------------------------------------------------------
# Pure math helpers (module-level for testability)
# ---------------------------------------------------------------------------

def _apply_levels(rgb, in_black, in_white, gamma, out_black, out_white):
    """Photoshop-style levels: remap input range, apply gamma, remap output range."""
    in_range = max(in_white - in_black, 1e-12)
    result = (rgb - in_black) / in_range
    result = np.clip(result, 0.0, 1.0)
    result = np.power(result, 1.0 / max(gamma, 1e-6))
    result = result * (out_white - out_black) + out_black
    return result


def _apply_brightness_contrast(rgb, brightness, contrast):
    """Simple brightness + contrast adjustment."""
    result = (rgb - 0.5) * (contrast + 1.0) + 0.5 + brightness
    return result


def _apply_hue_saturation(rgb, hue_shift, saturation, value):
    """Adjust HSV channels on an (N, 3) RGB array."""
    hsv = _rgb_to_hsv(rgb)
    hsv[:, 0] = (hsv[:, 0] + hue_shift - 0.5) % 1.0
    hsv[:, 1] = np.clip(hsv[:, 1] * saturation, 0.0, 1.0)
    hsv[:, 2] = np.clip(hsv[:, 2] * value, 0.0, 1.0)
    return _hsv_to_rgb(hsv)


def _rgb_to_hsv(rgb):
    """Convert (N, 3) RGB float array to (N, 3) HSV."""
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    delta = maxc - minc
    safe_delta = np.where(delta > 0, delta, 1.0)

    s = np.where(maxc > 0, delta / maxc, 0.0)

    rc = (maxc - r) / safe_delta
    gc = (maxc - g) / safe_delta
    bc = (maxc - b) / safe_delta

    h = np.where(
        r == maxc, bc - gc,
        np.where(g == maxc, 2.0 + rc - bc, 4.0 + gc - rc),
    )
    h = (h / 6.0) % 1.0
    h = np.where(delta > 0, h, 0.0)

    return np.column_stack([h, s, v]).astype(rgb.dtype)


def _hsv_to_rgb(hsv):
    """Convert (N, 3) HSV float array to (N, 3) RGB."""
    h, s, v = hsv[:, 0], hsv[:, 1], hsv[:, 2]
    i = (h * 6.0).astype(np.int32) % 6
    f = h * 6.0 - np.floor(h * 6.0)
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))

    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])

    return np.column_stack([r, g, b]).astype(hsv.dtype)


def _apply_layer_blend(base, blend, mode, factor):
    """Blend *blend* onto *base* using the specified blend *mode* and *factor*."""
    match mode:
        case "MIX":
            result = base + (blend - base) * factor
        case "MULTIPLY":
            result = base * (1.0 - factor) + base * blend * factor
        case "ADD":
            result = base + blend * factor
        case "SUBTRACT":
            result = base - blend * factor
        case "OVERLAY":
            lo = 2.0 * base * blend
            hi = 1.0 - 2.0 * (1.0 - base) * (1.0 - blend)
            overlay = np.where(base < 0.5, lo, hi)
            result = base + (overlay - base) * factor
        case "SCREEN":
            screen = 1.0 - (1.0 - base) * (1.0 - blend)
            result = base + (screen - base) * factor
        case _:
            result = base
    return result
