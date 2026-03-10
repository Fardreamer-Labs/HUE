# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from . import operators, property_groups, ui

packages = [property_groups, operators, ui]


def register():
    for package in packages:
        package.register()


def unregister():
    for package in reversed(packages):
        package.unregister()
