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
        webbrowser.open("https://github.com/tojynick/More-Colors")
        return {"FINISHED"}


class MC_OT_open_bug_report(BaseOperator):
    """Opens the GitHub issue tracker"""

    bl_label = "Report a Bug"
    bl_idname = "morecolors.open_bug_report"

    def execute(self, context):
        webbrowser.open("https://github.com/tojynick/More-Colors/issues")
        return {"FINISHED"}


class MC_OT_open_review(BaseOperator):
    """Opens the Blender Extensions page to leave a review"""

    bl_label = "Leave a Review"
    bl_idname = "morecolors.open_review"

    def execute(self, context):
        webbrowser.open("https://extensions.blender.org/add-ons/more-colors/")
        return {"FINISHED"}
