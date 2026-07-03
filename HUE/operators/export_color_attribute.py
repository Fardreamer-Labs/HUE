# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import re

import bpy
import numpy as np

from .base_operators import BaseOperator
from ..utilities.color_utilities import (
    bulk_get_colors,
    ensure_object_mode,
    get_active_color_attribute,
)

_ILLEGAL_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


def _sanitize_name(name):
    """Strip characters illegal in file names (also safe for Image data-block names)."""
    return _ILLEGAL_FILENAME_CHARS.sub("_", name.strip())


def _make_unique_export_path(export_path):
    """Return *export_path*, appending ``_001``, ``_002``... if it already exists."""
    directory = os.path.dirname(export_path)
    base_name = os.path.splitext(os.path.basename(export_path))[0]
    extension = os.path.splitext(export_path)[1] or ".png"

    unique_path = export_path
    index = 1
    while os.path.exists(unique_path):
        unique_path = os.path.join(directory, f"{base_name}_{index:03d}{extension}")
        index += 1
    return unique_path


class HUE_OT_make_texture(BaseOperator):
    """Rasterize the active color attribute into UV space as a new Image data-block"""

    bl_label = "Make Texture"
    bl_idname = "hue.make_texture"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            cls.poll_message_set("Select a mesh object")
            return False
        if len(obj.data.color_attributes) == 0:
            cls.poll_message_set("Active object has no color attributes")
            return False
        return True

    def execute(self, context):
        obj = context.active_object
        tool = context.scene.hue_export_texture_tool

        with ensure_object_mode(obj):
            mesh = obj.data

            uv_layer = mesh.uv_layers.active
            if uv_layer is None:
                if tool.auto_unwrap:
                    uv_layer = self._auto_unwrap(obj)
                    if uv_layer is None:
                        self.report(
                            {"ERROR"}, "Auto Unwrap failed to create a UV layer."
                        )
                        return {"CANCELLED"}
                else:
                    self.report(
                        {"ERROR"},
                        "Active object has no UV layer. Enable Auto Unwrap or add one manually.",
                    )
                    return {"CANCELLED"}

            color_attribute = get_active_color_attribute(obj)
            colors = bulk_get_colors(color_attribute)

            mesh.calc_loop_triangles()
            n_tris = len(mesh.loop_triangles)
            if n_tris == 0:
                self.report({"ERROR"}, "Active object has no faces to rasterize.")
                return {"CANCELLED"}

            tri_loops = np.empty(n_tris * 3, dtype=np.int32)
            mesh.loop_triangles.foreach_get("loops", tri_loops)
            tri_loops = tri_loops.reshape(n_tris, 3)

            n_loops = len(mesh.loops)
            uv_data = np.empty(n_loops * 2, dtype=np.float32)
            uv_layer.data.foreach_get("uv", uv_data)
            uv_data = uv_data.reshape(n_loops, 2)
            tri_uvs = uv_data[tri_loops]

            if color_attribute.domain == "CORNER":
                tri_colors = colors[tri_loops]
            else:
                tri_verts = np.empty(n_tris * 3, dtype=np.int32)
                mesh.loop_triangles.foreach_get("vertices", tri_verts)
                tri_verts = tri_verts.reshape(n_tris, 3)
                tri_colors = colors[tri_verts]

            width, height = tool.resolution_x, tool.resolution_y
            pixels = np.zeros((height, width, 4), dtype=np.float32)
            written = np.zeros((height, width), dtype=bool)

            self._rasterize_triangles(
                tri_uvs, tri_colors, pixels, written, width, height
            )

            if bpy.app.debug:
                coverage = written.sum() / written.size * 100
                print(
                    f"[HUE make_texture] triangles={n_tris} "
                    f"resolution={width}x{height} coverage={coverage:.2f}% "
                    f"color_min={pixels.min():.4f} color_max={pixels.max():.4f} "
                    f"color_mean={pixels.mean():.4f}"
                )

            self._dilate(pixels, written, tool.margin)

            if bpy.app.debug:
                coverage_after = written.sum() / written.size * 100
                print(
                    f"[HUE make_texture] after dilation (margin={tool.margin}) "
                    f"coverage={coverage_after:.2f}%"
                )

            image_name = (
                _sanitize_name(tool.export_name) or f"{obj.name}_{color_attribute.name}"
            )
            existing = bpy.data.images.get(image_name)
            replaced_image = existing is not None
            if existing is not None:
                bpy.data.images.remove(existing)

            img = bpy.data.images.new(
                name=image_name,
                width=width,
                height=height,
                alpha=True,
                float_buffer=True,
            )
            # IMPORTANT: colorspace must be assigned BEFORE the pixel buffer is
            # written. Reassigning Image.colorspace_settings.name AFTER
            # foreach_set()/update() resets the entire pixel buffer to (0,0,0,1)
            # (opaque black) — this was the actual cause of fully black exports.
            img.colorspace_settings.name = tool.colorspace
            img.pixels.foreach_set(pixels.ravel())
            img.update()

        tool.generated_image_name = img.name

        applied_material = None
        replaced_material = False
        if tool.apply_material:
            applied_material, replaced_material = self._apply_material(obj, img)

        replaced_notes = []
        if replaced_image:
            replaced_notes.append(f"image '{img.name}'")
        if replaced_material:
            replaced_notes.append(f"material '{applied_material.name}'")

        if replaced_notes:
            base_msg = f"Texture '{img.name}' created ({width}x{height})"
            if applied_material is not None:
                base_msg += f" and applied as material '{applied_material.name}'"
            self.report(
                {"WARNING"},
                f"{base_msg}; replaced existing {' and '.join(replaced_notes)}",
            )
        elif applied_material is not None:
            self.report(
                {"INFO"},
                f"Texture '{img.name}' created ({width}x{height}) and applied as material '{applied_material.name}'",
            )
        else:
            self.report({"INFO"}, f"Texture '{img.name}' created ({width}x{height})")
        return {"FINISHED"}

    @staticmethod
    def _apply_material(obj, img):
        """Create a simple Principled BSDF material using *img* as Base Color and assign it to *obj*.

        Replaces the object's active material slot if one exists, otherwise adds a new slot.
        Returns ``(material, replaced_existing)``.
        """
        mat_name = _sanitize_name(f"{img.name}_Material")
        existing = bpy.data.materials.get(mat_name)
        replaced_existing = existing is not None
        if existing is not None:
            bpy.data.materials.remove(existing)

        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        node_tree = mat.node_tree
        bsdf = node_tree.nodes.get("Principled BSDF")

        tex_node = node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        tex_node.location = (
            (bsdf.location.x - 300, bsdf.location.y) if bsdf else (-300, 0)
        )
        if bsdf is not None:
            node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

        if obj.data.materials:
            obj.data.materials[obj.active_material_index] = mat
        else:
            obj.data.materials.append(mat)

        return mat, replaced_existing

    @staticmethod
    def _auto_unwrap(obj):
        """Smart-UV-project *obj*, adding a UV layer first if it has none.

        Returns the resulting active UV layer, or ``None`` on failure.
        """
        mesh = obj.data
        if mesh.uv_layers.active is None:
            mesh.uv_layers.new(name="UVMap")

        view_layer = bpy.context.view_layer
        previous_active = view_layer.objects.active
        previous_selected = {o for o in view_layer.objects if o.select_get()}
        try:
            for o in view_layer.objects:
                o.select_set(o is obj)
            view_layer.objects.active = obj

            bpy.ops.object.mode_set(mode="EDIT")
            try:
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.uv.smart_project()
            finally:
                bpy.ops.object.mode_set(mode="OBJECT")
        finally:
            for o in view_layer.objects:
                o.select_set(o in previous_selected)
            view_layer.objects.active = previous_active

        return mesh.uv_layers.active

    # Rough per-batch memory budget (elements = batch_len * padded_h * padded_w).
    # Keeps peak memory for the w0/w1/w2/mask/color scratch arrays in the tens
    # of MB while still amortizing numpy call overhead across many triangles.
    _RASTER_BATCH_CELL_BUDGET = 2_000_000

    @classmethod
    def _rasterize_triangles(cls, tri_uvs, tri_colors, pixels, written, width, height):
        """Fill *pixels*/*written* by vectorized barycentric rasterization, batched
        across many triangles per numpy call instead of one call per triangle.

        The per-triangle Python loop's real cost isn't the barycentric math itself,
        it's the ~15 small numpy array allocations/dispatches made on *every*
        iteration -- this dominates once a mesh has more than a few thousand
        triangles. Triangles are grouped (in original mesh order, so overlap
        behavior stays identical to a strictly sequential loop) into variable-size
        batches bounded by ``_RASTER_BATCH_CELL_BUDGET``, and the barycentric
        test/interpolation is evaluated for the whole batch at once via
        broadcasting over an extra leading batch axis. Only the final scatter of
        each triangle's result back into ``pixels``/``written`` still loops
        per-triangle, but that step is just a cheap masked assignment.
        """
        n_tris = tri_uvs.shape[0]
        if n_tris == 0:
            return

        px_all = tri_uvs[:, :, 0] * width
        py_all = tri_uvs[:, :, 1] * height

        x_min_all = np.clip(np.floor(px_all.min(axis=1)), 0, width - 1).astype(np.int64)
        x_max_all = np.clip(np.ceil(px_all.max(axis=1)), 0, width - 1).astype(np.int64)
        y_min_all = np.clip(np.floor(py_all.min(axis=1)), 0, height - 1).astype(np.int64)
        y_max_all = np.clip(np.ceil(py_all.max(axis=1)), 0, height - 1).astype(np.int64)

        v0x, v1x, v2x = px_all[:, 0], px_all[:, 1], px_all[:, 2]
        v0y, v1y, v2y = py_all[:, 0], py_all[:, 1], py_all[:, 2]
        area_all = (v1x - v0x) * (v2y - v0y) - (v1y - v0y) * (v2x - v0x)

        valid = (
            (x_min_all <= x_max_all)
            & (y_min_all <= y_max_all)
            & (np.abs(area_all) >= 1e-9)
        )
        valid_idx = np.nonzero(valid)[0]
        if valid_idx.size == 0:
            return

        bw_all = (x_max_all - x_min_all + 1).astype(np.int64)
        bh_all = (y_max_all - y_min_all + 1).astype(np.int64)

        # Triangle-local (bbox-relative) vertex coords. The barycentric test is
        # translation-invariant, so this is numerically equivalent to the old
        # absolute-coordinate version -- it just lets triangles of different
        # sizes/positions in a batch share one small local pixel grid instead of
        # each needing its own full-canvas-sized one.
        x_min_f = x_min_all.astype(np.float32)
        y_min_f = y_min_all.astype(np.float32)
        lv0x, lv1x, lv2x = v0x - x_min_f, v1x - x_min_f, v2x - x_min_f
        lv0y, lv1y, lv2y = v0y - y_min_f, v1y - y_min_f, v2y - y_min_f

        budget = cls._RASTER_BATCH_CELL_BUDGET
        n_valid = valid_idx.size
        i = 0
        while i < n_valid:
            j = i + 1
            batch_w = int(bw_all[valid_idx[i]])
            batch_h = int(bh_all[valid_idx[i]])
            while j < n_valid:
                cand_w = max(batch_w, int(bw_all[valid_idx[j]]))
                cand_h = max(batch_h, int(bh_all[valid_idx[j]]))
                if cand_w * cand_h * (j - i + 1) > budget:
                    break
                batch_w, batch_h = cand_w, cand_h
                j += 1

            idx = valid_idx[i:j]
            k = idx.size
            w_pad, h_pad = batch_w, batch_h

            xs = np.arange(w_pad, dtype=np.float32) + 0.5
            ys = np.arange(h_pad, dtype=np.float32) + 0.5
            gx, gy = np.meshgrid(xs, ys)  # (h_pad, w_pad)
            gx = gx[np.newaxis, :, :]
            gy = gy[np.newaxis, :, :]

            b0x = lv0x[idx].reshape(k, 1, 1)
            b1x = lv1x[idx].reshape(k, 1, 1)
            b2x = lv2x[idx].reshape(k, 1, 1)
            b0y = lv0y[idx].reshape(k, 1, 1)
            b1y = lv1y[idx].reshape(k, 1, 1)
            b2y = lv2y[idx].reshape(k, 1, 1)
            area = area_all[idx].reshape(k, 1, 1)

            w0 = (b1x - b0x) * (gy - b0y) - (b1y - b0y) * (gx - b0x)
            w1 = (b2x - b1x) * (gy - b1y) - (b2y - b1y) * (gx - b1x)
            w2 = (b0x - b2x) * (gy - b2y) - (b0y - b2y) * (gx - b2x)

            mask = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | (
                (w0 <= 0) & (w1 <= 0) & (w2 <= 0)
            )

            bw_batch = bw_all[idx].reshape(k, 1, 1)
            bh_batch = bh_all[idx].reshape(k, 1, 1)
            mask &= (gx < bw_batch) & (gy < bh_batch)

            # w0 = edge(v0,v1,*) is zero along v0-v1, i.e. it's the weight for v2
            # (the opposite vertex). Likewise w1 -> weight for v0, w2 -> weight for v1.
            weight_v0 = w1 / area
            weight_v1 = w2 / area
            weight_v2 = w0 / area

            c0 = tri_colors[idx, 0][:, np.newaxis, np.newaxis, :]
            c1 = tri_colors[idx, 1][:, np.newaxis, np.newaxis, :]
            c2 = tri_colors[idx, 2][:, np.newaxis, np.newaxis, :]

            color = (
                weight_v0[..., np.newaxis] * c0
                + weight_v1[..., np.newaxis] * c1
                + weight_v2[..., np.newaxis] * c2
            )

            x_min_batch = x_min_all[idx]
            y_min_batch = y_min_all[idx]
            bw_list = bw_all[idx]
            bh_list = bh_all[idx]

            # Scatter each triangle's result back in original mesh order, so a
            # later triangle overwrites an earlier one on overlapping UV islands
            # exactly like the old strictly-sequential loop did.
            for n in range(k):
                bw_n, bh_n = int(bw_list[n]), int(bh_list[n])
                m = mask[n, :bh_n, :bw_n]
                if not m.any():
                    continue
                x0, y0 = int(x_min_batch[n]), int(y_min_batch[n])
                sub_pixels = pixels[y0 : y0 + bh_n, x0 : x0 + bw_n]
                sub_written = written[y0 : y0 + bh_n, x0 : x0 + bw_n]
                sub_color = color[n, :bh_n, :bw_n]
                sub_pixels[m] = sub_color[m]
                sub_written[m] = True

            i = j

    @staticmethod
    def _dilate(pixels, written, margin):
        """Grow written pixels outward by *margin* iterations to bleed past UV seams."""
        for _ in range(margin):
            if written.all():
                break
            filled = pixels.copy()
            fmask = written.copy()
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                shifted_written = np.roll(written, shift=(dy, dx), axis=(0, 1))
                shifted_pixels = np.roll(pixels, shift=(dy, dx), axis=(0, 1))
                candidate = (~written) & shifted_written
                if dy == -1:
                    candidate[-1, :] = False
                elif dy == 1:
                    candidate[0, :] = False
                if dx == -1:
                    candidate[:, -1] = False
                elif dx == 1:
                    candidate[:, 0] = False
                filled[candidate] = shifted_pixels[candidate]
                fmask |= candidate
            pixels[...] = filled
            written[...] = fmask


class HUE_OT_export_color_attribute(BaseOperator):
    """Save the texture created by 'Make Texture' to a PNG file on disk"""

    bl_label = "Export as PNG"
    bl_idname = "hue.export_color_attribute"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        tool = context.scene.hue_export_texture_tool
        if (
            not tool.generated_image_name
            or tool.generated_image_name not in bpy.data.images
        ):
            cls.poll_message_set("Make a texture first")
            return False
        return True

    def execute(self, context):
        tool = context.scene.hue_export_texture_tool
        img = bpy.data.images.get(tool.generated_image_name)
        if img is None:
            self.report({"ERROR"}, "No texture found. Click 'Make Texture' first.")
            return {"CANCELLED"}

        export_path = self._build_export_path(img.name, tool)

        # save_render() always applies the scene's full color management (View
        # Transform / Look / Exposure / Gamma) on top of the buffer, since it's
        # designed for writing scene-linear render results to disk. Our buffer is
        # already gamma-encoded sRGB data (not scene-linear), so the View Transform
        # (e.g. AgX, Blender's default since 4.0) must be neutralized or it will
        # double-encode/crush the colors — this is what caused fully black exports.
        image_settings = context.scene.render.image_settings
        view_settings = context.scene.view_settings
        original_format = image_settings.file_format
        original_depth = image_settings.color_depth
        original_mode = image_settings.color_mode
        original_view_transform = view_settings.view_transform
        original_look = view_settings.look
        original_exposure = view_settings.exposure
        original_gamma = view_settings.gamma
        try:
            image_settings.file_format = "PNG"
            image_settings.color_depth = tool.color_depth
            image_settings.color_mode = "RGBA"
            view_settings.view_transform = "Standard"
            view_settings.look = "None"
            view_settings.exposure = 0.0
            view_settings.gamma = 1.0

            if bpy.app.debug:
                print(
                    f"[HUE export_color_attribute] saving to {export_path} "
                    f"depth={tool.color_depth} is_float={img.is_float} "
                    f"colorspace={img.colorspace_settings.name}"
                )

            img.save_render(export_path, scene=context.scene)

            if bpy.app.debug:
                saved_size = (
                    os.path.getsize(export_path) if os.path.exists(export_path) else -1
                )
                print(
                    f"[HUE export_color_attribute] saved file size={saved_size} bytes"
                )
        finally:
            image_settings.file_format = original_format
            image_settings.color_depth = original_depth
            image_settings.color_mode = original_mode
            view_settings.view_transform = original_view_transform
            view_settings.look = original_look
            view_settings.exposure = original_exposure
            view_settings.gamma = original_gamma

        self.report({"INFO"}, f"Exported to {export_path}")
        return {"FINISHED"}

    @staticmethod
    def _build_export_path(image_name, tool):
        custom_name = _sanitize_name(tool.export_name)
        file_name = custom_name if custom_name else image_name
        if not file_name.lower().endswith(".png"):
            file_name += ".png"

        directory = tool.export_path
        if not directory:
            directory = (
                os.path.dirname(bpy.data.filepath)
                if bpy.data.filepath
                else os.path.expanduser("~")
            )
        else:
            directory = bpy.path.abspath(directory)
            os.makedirs(directory, exist_ok=True)

        full_path = os.path.join(directory, file_name)
        if tool.overwrite_existing:
            return full_path
        return _make_unique_export_path(full_path)
