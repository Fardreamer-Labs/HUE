# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import webbrowser

from .base_operators import BaseOperator


class HUE_OT_open_documentation(BaseOperator):
    """Opens a github page with documentation"""

    bl_label = "Need help? Read the docs!"
    bl_idname = "hue.open_documentation"

    def execute(self, context):
        webbrowser.open("https://github.com/Fardreamer-Labs/HUE")
        return {"FINISHED"}


class HUE_OT_open_bug_report(BaseOperator):
    """Opens the GitHub issue tracker"""

    bl_label = "Report a Bug"
    bl_idname = "hue.open_bug_report"

    def execute(self, context):
        webbrowser.open("https://github.com/Fardreamer-Labs/HUE/issues")
        return {"FINISHED"}


class HUE_OT_open_review(BaseOperator):
    """Opens the Blender Extensions page to leave a review"""

    bl_label = "Leave a Review"
    bl_idname = "hue.open_review"

    def execute(self, context):
        webbrowser.open("https://extensions.blender.org/add-ons/hue/")
        return {"FINISHED"}
