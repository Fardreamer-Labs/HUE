# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import operators, preferences, property_groups, ui
from .utilities.palette_utilities import register_handlers, unregister_handlers

packages = [property_groups, operators, ui]


def register():
    preferences.register()

    for package in packages:
        package.register()

    register_handlers()

    # Startup defaults — own handler + timer so they survive file loads
    bpy.app.handlers.load_post.append(preferences._apply_startup_defaults)
    bpy.app.timers.register(preferences._apply_startup_defaults, first_interval=0)


def unregister():
    if preferences._apply_startup_defaults in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(preferences._apply_startup_defaults)

    unregister_handlers()

    for package in reversed(packages):
        package.unregister()
        
    preferences.unregister()
