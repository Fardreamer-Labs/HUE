from bpy.props import FloatVectorProperty, IntProperty
from bpy.types import PropertyGroup

class SimpleFillToolProperties(PropertyGroup):
    preset_count: IntProperty(default=4, min=1, max=10)
    preset_max_count = 10

    selected_color: FloatVectorProperty(
        name = "Color",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1, 1, 1, 1),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_1: FloatVectorProperty(
        name = "Preset Color 1",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 0.050, 0.078, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_2: FloatVectorProperty(
        name = "Preset Color 2",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 0.743, 0.050, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_3: FloatVectorProperty(
        name = "Preset Color 3",
        description = "Choose a color",
        subtype = "COLOR",
        default = (0.498, 0.788, 0.039, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_4: FloatVectorProperty(
        name = "Preset Color 4",
        description = "Choose a color",
        subtype = "COLOR",
        default = (0.038, 0.490, 0.768, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_5: FloatVectorProperty(
        name = "Preset Color 5",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 1.000, 1.000, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_6: FloatVectorProperty(
        name = "Preset Color 6",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 1.000, 1.000, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_7: FloatVectorProperty(
        name = "Preset Color 7",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 1.000, 1.000, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_8: FloatVectorProperty(
        name = "Preset Color 8",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 1.000, 1.000, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_9: FloatVectorProperty(
        name = "Preset Color 9",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 1.000, 1.000, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )

    preset_color_10: FloatVectorProperty(
        name = "Preset Color 10",
        description = "Choose a color",
        subtype = "COLOR",
        default = (1.000, 1.000, 1.000, 1.000),
        min = 0, 
        max = 1,
        size = 4
    )
