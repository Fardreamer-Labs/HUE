# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

DEBUG_MODE = False


def debug(msg):
    """Print debug message to Blender console when DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(f"[MC Debug] {msg}")
