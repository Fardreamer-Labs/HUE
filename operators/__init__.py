import bpy
from . import display_vertex_colors, reset_vertex_colors, add_random_color, open_documentation, add_color_by_position, simple_fill

# Add new operator classes here
classes = [
    display_vertex_colors.MORECOLORS_OT_display_vertex_colors,

    add_random_color.MORECOLORS_OT_add_random_color,
    open_documentation.MORECOLORS_OT_open_documentation,
    reset_vertex_colors.MORECOLORS_OT_reset_color,

    add_color_by_position.MORECOLORS_OT_add_color_by_position,
    add_color_by_position.MORECOLORS_OT_initialize_color_by_position_tool,
    add_color_by_position.MORECOLORS_OT_reset_color_by_position_gradient,

    simple_fill.MORECOLORS_OT_simple_fill,
    simple_fill.MORECOLORS_OT_select_preset_color,
    simple_fill.MORECOLORS_OT_apply_preset_color,
    simple_fill.MORECOLORS_OT_apply_new_preset_color
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
