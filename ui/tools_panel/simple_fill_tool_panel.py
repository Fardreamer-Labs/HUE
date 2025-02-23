from bpy.types import Panel
from ..base_panel_info import BasePanelInfo

class MORECOLORS_PT_simple_fill_tool_panel(BasePanelInfo, Panel):
    bl_label = "Simple Fill"
    bl_idname = "MORECOLORS_PT_simple_fill_tool_panel"
    bl_parent_id = "MORECOLORS_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 0

    def draw(self, context):
        layout = self.layout

        simple_fill_tool = context.scene.more_colors_simple_fill_tool

        row = layout.row()
        row.label(text = "Fills a selection with color.")

        layout.separator()

        row = layout.row()
        row.label(text = "Presets", icon = "COLOR")

        column = layout.column(align = True)


        for i in range(1, simple_fill_tool.preset_count + 1):
            split = column.split()
            row = split.row()
            row.prop(simple_fill_tool, "preset_color_" + str(i), text = "")
            split.operator("morecolors.select_preset_color", icon = "EYEDROPPER").preset_name = "preset_color_" + str(i)
            split.operator("morecolors.apply_preset_color", icon = "BRUSH_DATA").preset_name = "preset_color_" + str(i)

        if simple_fill_tool.preset_count < simple_fill_tool.preset_max_count:
            layout.separator()
            row = layout.row()
            row.prop(simple_fill_tool, "selected_color", text = "")
            row.operator("morecolors.apply_new_preset_color", icon = "BRUSH_DATA")

        layout.separator()
        row = layout.row()
        row.prop(simple_fill_tool, "selected_color", text = "")
        row.operator("morecolors.simple_fill", icon = "BRUSH_DATA")
