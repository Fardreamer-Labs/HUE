from ..utilities.color_utilities import get_masked_color, get_active_color_attribute
from .base_operators import BaseColorOperator
import bpy

class MORECOLORS_OT_simple_fill(BaseColorOperator):
    """Applies a selected color to selected object(s) or part of the mesh"""

    bl_label = "Apply"
    bl_idname = "morecolors.simple_fill"

    def execute(self, context):
        if not context.selected_objects:
            self.report({"ERROR"}, "No objects selected!")
            return {"CANCELLED"}
        
        scene = context.scene
        global_color_settings = scene.more_colors_global_color_settings
        simple_fill_tool = scene.more_colors_simple_fill_tool

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            
            # We meed tp change mode to object in order to apply vertex colors
            was_in_edit_mode = (obj.mode == "EDIT")
            if was_in_edit_mode:
                bpy.ops.object.mode_set(mode = "OBJECT")

            color_attribute = get_active_color_attribute(obj)

            match color_attribute.domain:
                case "CORNER":
                    select_mode = context.tool_settings.mesh_select_mode

                    # Point Selection
                    if select_mode[0]:
                        for vert in obj.data.vertices:
                            if vert.select:
                                for poly in obj.data.polygons:
                                    for loop_index in poly.loop_indices:

                                        # Check if the loop belongs to the selected vertex
                                        loop_vert_index = obj.data.loops[loop_index].vertex_index
                                        if loop_vert_index == vert.index:  
                                            data = color_attribute.data[loop_index]
                                            data.color_srgb = get_masked_color(data.color_srgb, simple_fill_tool.selected_color, global_color_settings.get_mask())

                    # Edge Selection
                    if select_mode[1]:
                        for edge in obj.data.edges:
                            if edge.select:
                                for poly in obj.data.polygons:
                                    for loop_index in poly.loop_indices:

                                        # Check if the loop's vertex index belongs to the selected edge
                                        loop_vert_index = obj.data.loops[loop_index].vertex_index
                                        if loop_vert_index in edge.vertices:
                                            data = color_attribute.data[loop_index]
                                            data.color_srgb = get_masked_color(data.color_srgb, simple_fill_tool.selected_color, global_color_settings.get_mask())

                    # Face Selection
                    if select_mode[2]:
                        for poly in obj.data.polygons:
                            if poly.select:
                                for loop_index in poly.loop_indices:
                                    data = color_attribute.data[loop_index]
                                    data.color_srgb = get_masked_color(data.color_srgb, simple_fill_tool.selected_color, global_color_settings.get_mask())


                # Since "point" domain stores colors only for vertices, we can modify their color directly, without worrying about the selection mode or loop indices
                case "POINT":
                    for p in obj.data.vertices:
                        if p.select:
                            data = color_attribute.data[p.index]
                            data.color_srgb = get_masked_color(data.color_srgb, simple_fill_tool.selected_color, global_color_settings.get_mask())

            obj.data.update()

            if was_in_edit_mode:
                bpy.ops.object.mode_set(mode = "EDIT")

        self.report({"INFO"}, "Vertex colors assigned successfully!")
        return {"FINISHED"}
    

class MORECOLORS_OT_select_preset_color(bpy.types.Operator):
    """Selects the preset's color"""

    bl_label = "Select"
    bl_idname = "morecolors.select_preset_color"

    preset_name: bpy.props.StringProperty(options = {"HIDDEN"})
    
    def execute(self, context):
        scene = context.scene
        simple_fill_tool = scene.more_colors_simple_fill_tool

        simple_fill_tool.selected_color = getattr(simple_fill_tool, self.preset_name)

        return {"FINISHED"}
    

class MORECOLORS_OT_apply_preset_color(BaseColorOperator):
    """Applies the preset color to selected object(s) or part of the mesh"""

    bl_label = "Quick Apply"
    bl_idname = "morecolors.apply_preset_color"

    preset_name: bpy.props.StringProperty(options = {"HIDDEN"})
    
    
    def execute(self, context):
        scene = context.scene
        simple_fill_tool = scene.more_colors_simple_fill_tool

        # Copy the color data, instead of creating a reference
        previous_selected_color = list(simple_fill_tool.selected_color)

        simple_fill_tool.selected_color = getattr(simple_fill_tool, self.preset_name)
        bpy.ops.morecolors.simple_fill()
        simple_fill_tool.selected_color = previous_selected_color

        return {"FINISHED"}

class MORECOLORS_OT_apply_new_preset_color(BaseColorOperator):
    bl_label = "Add Color"
    bl_idname = "morecolors.apply_new_preset_color"

    preset_name: bpy.props.StringProperty(options = {"HIDDEN"})
    

    def execute(self, context):
        scene = context.scene
        simple_fill_tool = scene.more_colors_simple_fill_tool

        preset_attr = f"preset_color_{simple_fill_tool.preset_count + 1}"
        setattr(simple_fill_tool, preset_attr, simple_fill_tool.selected_color)
        
        setattr(simple_fill_tool, 'preset_count', simple_fill_tool.preset_count + 1)

        return {"FINISHED"}
