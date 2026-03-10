# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import webbrowser

from .base_operators import BaseOperator


class MC_OT_open_documentation(BaseOperator):
    """Opens a github page with documentation"""

    bl_label = "Need help? Read the docs!"
    bl_idname = "morecolors.open_documentation"

    def execute(self, context):
        url = "https://github.com/tojynick/More-Colors"
        webbrowser.open(url)

        return {"FINISHED"}
