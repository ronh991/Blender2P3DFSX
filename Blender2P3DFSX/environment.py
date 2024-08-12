#####################################################################################
#
#  Blender2P3D/FSX
#
#####################################################################################
#
# The addon in its current version is the hard work of many members of the
# fsdeveloper.com forum. The original FSX2Blender addon was developed by:
#   Felix Owono-Ateba
#   Ron Haertel
#   Kris Pyatt (2017)
#   Manochvarma Raman (2018)
#
# This current incarnation of the addon uses most of the original algorithms,
# but with an updated UI and compatibility for Blender 2.8x. Parts of the
# original exporter script have been re-written to accommodate Blender's new
# material workflow and to add PBR support to the addon (P3D v4.4+/v5 only).
#
# The conversion for Blender 2.8x was done by:
#   Otmar Nitsche (2019/2020)
#
# Further enhancement to the material workflow were coded by:
#   David Hoeffgen (2020)
#
# For information on how to use the addon, please visit:
# https://www.fsdeveloper.com/wiki/index.php?title=Blender2P3D/FSX
#
# If you have any questions, or suggestions, visit the support thread under:
# https://www.fsdeveloper.com/forum/forums/blender.136/
#
# For the original Blender2FSX addon, visit:
# https://www.fsdeveloper.com/forum/threads/blender2fsx-p3d-v0-9-5-onwards.442082/
#
# Special thanks go to Arno Gerretsen and Bill Womack for their input during the
# development and testing of the addon.
#
# The software is licensed under GNU General Public License (GNU-GPL-3).
# Feel free to use it as you see fit, both for freeware and commercial projects.
# If you have suggestions for changes, use the support thread in the
# fsdeveloper.com forum. If you would like to get involved in the development
# of the addon, contact any of the authors mentioned above to coordinate
# the effort.
#
#####################################################################################
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#####################################################################################

import bpy
import bpy.types
from bpy.types import Material, Image
from bpy.props import IntProperty, BoolProperty, StringProperty, FloatProperty, EnumProperty, FloatVectorProperty, PointerProperty

from . li_visibility import *
from . li_animation import *
from . li_mouserect import *
from . li_scenery import *
from . func_material import *
from . func_scenery import *


class Environment():

    # Use this function to  the blender-native material settings
    def switch_material(self, context):
        # TODO confirmation needed here! No idea how... ON
        # bpy.ops.ui.msgbox('INVOKE_DEFAULT')

        mat = context.active_object.active_material
        if mat.fsxm_material_mode == 'PBR':
            MaterialUtil.CreatePBRShader(mat)
            print("Switched to PBR material.")
        elif mat.fsxm_material_mode == 'FSX':
            MaterialUtil.CreateSpecShader(mat)
            print("Switched to specular material.")
        else:
            print("Switched to non-sim material.")

    def switch_sdk(self, context):
        print("Selected SDK: %s" % context.scene.global_sdk)

    def switch_pbr_blending(self, context):
        mat = context.active_object.active_material
        if mat.fsxm_rendermode == 'Opaque':
            MaterialUtil.MakeOpaque(mat)
        elif mat.fsxm_rendermode == 'Masked':
            MaterialUtil.MakeMasked(mat)
        elif mat.fsxm_rendermode == 'Translucent':
            MaterialUtil.MakeTranslucent(mat)

    def toggle_zbias(self, context):
        mat = context.active_object.active_material
        if mat.fsxm_zbias < 0:
            mat.fsxm_noshadow = True
            mat.fsxm_nozwrite = True

    def switch_environmentmap(self, context):
        mat = context.active_object.active_material
        if mat.fsxm_environmentmap is not None:
            mat.fsxm_globenv = False
        else:
            mat.fsxm_globenv = True

    def switch_locations(self, context):
        bpy.ops.fsx.load_location('INVOKE_DEFAULT')

    def setDetailScale(self, context):
        mat = context.active_object.active_material
        try:
            if mat.fsxm_material_mode == 'FSX':
                mat.node_tree.nodes["Detail Scale"].inputs["Scale"].default_value[0] = mat.fsxm_detailscale
                mat.node_tree.nodes["Detail Scale"].inputs["Scale"].default_value[1] = mat.fsxm_detailscale
                mat.node_tree.nodes["Detail Scale"].inputs["Scale"].default_value[2] = mat.fsxm_detailscale
                mat.node_tree.nodes["Detail Scale"].inputs["Rotation"].default_value[2] = mat.fsxm_DetailRotation * 3.141592653589793 / 180
                mat.node_tree.nodes["Detail Scale"].inputs["Location"].default_value[0] = mat.fsxm_DetailOffsetU
                mat.node_tree.nodes["Detail Scale"].inputs["Location"].default_value[1] = mat.fsxm_DetailOffsetV
            elif mat.fsxm_material_mode == 'PBR':
                mat.node_tree.nodes["Detail Scale"].inputs["Scale"].default_value[0] = mat.fsxm_detail_scale_x
                mat.node_tree.nodes["Detail Scale"].inputs["Scale"].default_value[1] = mat.fsxm_detail_scale_y
        except:
            pass

    def setBumpScale(self, context):
        mat = context.active_object.active_material
        try:
            if mat.fsxm_material_mode == 'FSX':
                mat.node_tree.nodes["Bump Scale"].inputs["Scale"].default_value[0] = mat.fsxm_bumpscale
                mat.node_tree.nodes["Bump Scale"].inputs["Scale"].default_value[1] = mat.fsxm_bumpscale
                mat.node_tree.nodes["Bump Scale"].inputs["Scale"].default_value[2] = mat.fsxm_bumpscale
            elif mat.fsxm_material_mode == 'PBR':
                mat.node_tree.nodes["Bump Scale"].inputs["Scale"].default_value[0] = mat.fsxm_normal_scale_x
                mat.node_tree.nodes["Bump Scale"].inputs["Scale"].default_value[1] = mat.fsxm_normal_scale_y
        except:
            pass

    def setDetailBlend(self, context):
        mat = context.active_object.active_material

        try:
            if mat.fsxm_DetailBlendMode == 'Blend':
                mat.node_tree.nodes["Detail Blend"].blend_type = 'OVERLAY'
            elif mat.fsxm_DetailBlendMode == 'Multiply':
                mat.node_tree.nodes["Detail Blend"].blend_type = 'MULTIPLY'
        except:
            pass

    def matchdiffuse(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Diffuse", None) is not None:
            mat.node_tree.nodes["Diffuse"].image = mat.fsxm_diffusetexture
            if mat.fsxm_diffusetexture is not None:
                if mat.fsxm_diffusetexture.name.split(".")[len(mat.fsxm_diffusetexture.name.split(".")) - 1] == 'dds':
                    mat.node_tree.nodes["Diffuse"].texture_mapping.scale[1] = -1
                else:
                    mat.node_tree.nodes["Diffuse"].texture_mapping.scale[1] = 1

    def matchnormal(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Normal", None) is not None:
            mat.node_tree.nodes["Normal"].image = mat.fsxm_bumptexture
            mat.node_tree.nodes["Normal"].image.colorspace_settings.name = 'Non-Color'
            if mat.fsxm_bumptexture is not None:
                if mat.fsxm_bumptexture.name.split(".")[len(mat.fsxm_bumptexture.name.split(".")) - 1] == 'dds':
                    mat.node_tree.nodes["Normal"].texture_mapping.scale[1] = -1
                    if mat.node_tree.nodes.get("Mix Normals", None) is not None:
                        mat.node_tree.nodes["Mix Normals"].inputs["Fac"].default_value = 1
                else:
                    mat.node_tree.nodes["Normal"].texture_mapping.scale[1] = 1
                    if mat.node_tree.nodes.get("Mix Normals", None) is not None:
                        mat.node_tree.nodes["Mix Normals"].inputs["Fac"].default_value = 0

            if mat.node_tree.nodes.get("Normal Map", None) is not None:
                if mat.fsxm_bumptexture is None:
                    mat.node_tree.nodes["Normal Map"].inputs["Strength"].default_value = 0
                else:
                    mat.node_tree.nodes["Normal Map"].inputs["Strength"].default_value = 1

    def matchmetallic(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Metallic", None) is not None:
            mat.node_tree.nodes["Metallic"].image = mat.fsxm_metallictexture
            mat.node_tree.nodes["Metallic"].image.colorspace_settings.name = 'Non-Color'
            if mat.fsxm_metallictexture is not None:
                if mat.fsxm_metallictexture.name.split(".")[len(mat.fsxm_metallictexture.name.split(".")) - 1] == 'dds':
                    mat.node_tree.nodes["Metallic"].texture_mapping.scale[1] = -1
                else:
                    mat.node_tree.nodes["Metallic"].texture_mapping.scale[1] = 1

    def matchspecular(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("specular", None) is not None:       # "specular" must not be capitalized like other node names. See line 132 func_material.py   Dave_W
            mat.node_tree.nodes["specular"].image = mat.fsxm_speculartexture
            if mat.fsxm_speculartexture is not None:
                if mat.fsxm_speculartexture.name.split(".")[len(mat.fsxm_speculartexture.name.split(".")) - 1] == 'dds':
                    mat.node_tree.nodes["specular"].texture_mapping.scale[1] = -1
                else:
                    mat.node_tree.nodes["specular"].texture_mapping.scale[1] = 1

    def matchdetail(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Detail", None) is not None:
            mat.node_tree.nodes["Detail"].image = mat.fsxm_detailtexture
            if mat.fsxm_detailtexture is not None:
                if mat.fsxm_detailtexture.name.split(".")[len(mat.fsxm_detailtexture.name.split(".")) - 1] == 'dds':
                    mat.node_tree.nodes["Detail"].texture_mapping.scale[1] = -1
                else:
                    mat.node_tree.nodes["Detail"].texture_mapping.scale[1] = 1

        if mat.node_tree.nodes.get("Detail Blend", None) is not None:
            if mat.fsxm_detailtexture is None:
                mat.node_tree.nodes["Detail Blend"].inputs["Fac"].default_value = 0
            else:
                mat.node_tree.nodes["Detail Blend"].inputs["Fac"].default_value = 1

    def matchemissive(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Emissive", None) is not None:
            mat.node_tree.nodes["Emissive"].image = mat.fsxm_emissivetexture
            if mat.fsxm_emissivetexture is not None:
                if mat.fsxm_emissivetexture.name.split(".")[len(mat.fsxm_emissivetexture.name.split(".")) - 1] == 'dds':
                    mat.node_tree.nodes["Emissive"].texture_mapping.scale[1] = -1
                else:
                    mat.node_tree.nodes["Emissive"].texture_mapping.scale[1] = 1

    # copied and edited from matchmetallic       Dave_W
    def matchclearcoat(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Clearcoat", None) is not None:
            mat.node_tree.nodes["Clearcoat"].image = mat.fsxm_clearcoattexture
            mat.node_tree.nodes["Clearcoat"].image.colorspace_settings.name = 'Non-Color'
            if mat.fsxm_clearcoattexture is not None:
                if (mat.fsxm_clearcoattexture.name.split(".")[len(mat.fsxm_clearcoattexture.name.split(".")) - 1] == 'dds'):
                    mat.node_tree.nodes["Clearcoat"].texture_mapping.scale[1] = -1
                else:
                    mat.node_tree.nodes["Clearcoat"].texture_mapping.scale[1] = 1

    bpy.types.Scene.fsx_modeldefpath = bpy.props.StringProperty(name="modeldef", default="modeldef.xml has not been registered yet", description="Path to modeldef.xml")
    bpy.types.Scene.fsx_sdkpath = bpy.props.StringProperty(name="sdk", default="sdk has not been registered yet", description="Path to sdk")

    # Scene Properties

    # Integer
    bpy.types.Scene.fsx_attachpoint_counter = bpy.props.IntProperty(default=0, min=0)
    bpy.types.Scene.active_fsx_visibility = bpy.props.IntProperty(default=-1, min=-1)
    bpy.types.Scene.active_fsx_anim = bpy.props.IntProperty(default=-1, min=-1)
    bpy.types.Scene.active_fsx_mouserect = bpy.props.IntProperty(default=-1, min=-1)
    bpy.types.Scene.active_fsx_location = bpy.props.IntProperty(default=-1, min=-1, update=switch_locations)
    # Collection
    bpy.types.Scene.fsx_anims = bpy.props.CollectionProperty(type=FSXAnimation)
    bpy.types.Scene.p3d_anims = bpy.props.CollectionProperty(type=FSXAnimation)  # added for ronh code kp
    bpy.types.Scene.fsx_visibility = bpy.props.CollectionProperty(type=FSXVisibility)
    bpy.types.Scene.fsx_mouserects = bpy.props.CollectionProperty(type=FSXMouseRect)
    bpy.types.Scene.p3d_mouserects = bpy.props.CollectionProperty(type=FSXMouseRect)  # added for ronh code kp
    bpy.types.Scene.fsx_locations = bpy.props.CollectionProperty(type=FSXLocation)
    # Float:
    bpy.types.Scene.fsx_bounding_min_x = bpy.props.FloatProperty(name="X", default=-1.0, description="min X of the bounding box")
    bpy.types.Scene.fsx_bounding_min_y = bpy.props.FloatProperty(name="Y", default=-1.0, description="min Y of the bounding box")
    bpy.types.Scene.fsx_bounding_min_z = bpy.props.FloatProperty(name="Z", default=-1.0, description="min Z of the bounding box")
    bpy.types.Scene.fsx_bounding_max_x = bpy.props.FloatProperty(name="X", default=1.0, description="max X of the bounding box")
    bpy.types.Scene.fsx_bounding_max_y = bpy.props.FloatProperty(name="Y", default=1.0, description="max Y of the bounding box")
    bpy.types.Scene.fsx_bounding_max_z = bpy.props.FloatProperty(name="Z", default=1.0, description="max Z of the bounding box")
    bpy.types.Scene.fsx_radius = bpy.props.FloatProperty(name="Radius", default=2.0, min=0.0, description="Radius")
    # Enum
    bpy.types.Scene.global_sdk = bpy.props.EnumProperty(items=(('p3dv6', "P3Dv6 SDK", ""), ('p3dv5', "P3Dv5 SDK", ""), ('p3dv4', "P3Dv4 SDK", ""), ('p3dv3', "P3Dv3 SDK", ""), ('p3dv2', "P3Dv2 SDK", ""), ('p3dv1', "P3Dv1/ FSX:SE SDK", ""),
                                                               ('fsx', "FSX:A SDK", ""),), name="", description="Select an SDK", update=switch_sdk)
    bpy.types.Scene.fsx_scenery_complexity = bpy.props.EnumProperty(items=(('VERY_SPARSE', "very sparse", ""), ('SPARSE', "sparse", ""), ('NORMAL', "normal", ""), ('DENSE', "dense", ""), ('VERY_DENSE', "very dense", ""),), name="", default='NORMAL', description="Scenery complexity")
    bpy.types.Scene.fsx_altitude_unit = bpy.props.EnumProperty(items=(('M', "m", ""), ('F', "ft", ""),), name="", default='M', description="Unit of measurement")
    # String
    bpy.types.Scene.fsx_guid = bpy.props.StringProperty(name="", default="", description="The file's GUID")
    bpy.types.Scene.fsx_friendly = bpy.props.StringProperty(name="", default="", description="Enter friendly name")

    bpy.types.Scene.fsx_Latitude = bpy.props.StringProperty(name="", default="0.0", description="The location file Latitude")
    bpy.types.Scene.fsx_Longitude = bpy.props.StringProperty(name="", default="0.0", description="The location file Longitude")
    bpy.types.Scene.fsx_Altitude = bpy.props.FloatProperty(name="Altitude", default=0.0, description="The location file Altitude")
    bpy.types.Scene.fsx_Pitch = bpy.props.FloatProperty(name="Pitch", default=0.0, min=0, max=360, description="The location file Pitch")
    bpy.types.Scene.fsx_Bank = bpy.props.FloatProperty(name="Bank", default=0.0, min=0, max=360, description="The location file Bank")
    bpy.types.Scene.fsx_Heading = bpy.props.FloatProperty(name="Heading", default=0.0, min=0, max=360, description="The location file Heading")

    bpy.types.Scene.fsx_platform_name = bpy.props.StringProperty(name="Name", default="", description="Name must be unique across the scene")
    bpy.types.Scene.fsx_effect_name = bpy.props.StringProperty(name="Name", default="", description="Attachpoint name: must be unique across the scene")
    bpy.types.Scene.fsx_effect_file = bpy.props.StringProperty(name="Effect", default="", description="Enter Effect file to attach (no .fx extension)")
    bpy.types.Scene.fsx_effect_params = bpy.props.StringProperty(name="Params", default="", description="Effect parameters, refer to SDK for usage")
    bpy.types.Scene.fsx_location_name = bpy.props.StringProperty(name="", default="", description="Name under which a location is saved")
    # Booleans
    # Select SDK booleans
    bpy.types.Scene.fsx_bool_autoDetectSDK = bpy.props.BoolProperty(name="Auto Detect SDK", default=True, description="Sets Auto Detect of selected SDK")

    # Attach Tool booleans
    bpy.types.Scene.fsx_bool_effect = bpy.props.BoolProperty(name="Effect", default=False, description="Attach Effect to selected object")
    bpy.types.Scene.fsx_bool_vis = bpy.props.BoolProperty(name="Visibility", default=False, description="Attach visibility Tag to selected object")
    bpy.types.Scene.fsx_bool_mouserect = bpy.props.BoolProperty(name="Mouse Rect", default=False, description="Attach Mouse Clickspot to selected object")
    bpy.types.Scene.fsx_bool_platform = bpy.props.BoolProperty(name="Platform", default=False, description="Attach Platform to selected object")
    bpy.types.Scene.fsx_bool_nocrash = bpy.props.BoolProperty(name="No Crash", default=False, description="Set No Crash for selected object")
    bpy.types.Scene.fsx_bool_empty_attach_point = bpy.props.BoolProperty(name="Empty", default=False, description="Create an empty attach point")

    # Scenery Properties booleans
    bpy.types.Scene.fsx_bool_altitude_is_agl = bpy.props.BoolProperty(name="Altitude is AGL", default=False, description="Sets the altitude of object to AGL")
    bpy.types.Scene.fsx_bool_noAutogenSup = bpy.props.BoolProperty(name="NoAutoGenSuppression", default=False, description="Set No Auto Gen Suppresion for active Project")
    bpy.types.Scene.fsx_bool_loadlocation = bpy.props.BoolProperty(name="Load", default=False, description="Load previously saved location(s)")

    # File Properties booleans
    bpy.types.Scene.fsx_bool_overrideBoundingBox = bpy.props.BoolProperty(name="Override bounding box?", default=False, description="Define a bounding box for the model")
    bpy.types.Scene.fsx_bool_overrideRadius = bpy.props.BoolProperty(name="Override radius?", default=False, description="Define a radius for the model")

    # Object Properties
    bpy.types.Object.fsx_anim_tag = bpy.props.StringProperty(name="", default="")
    bpy.types.Object.fsx_anim_length = bpy.props.StringProperty(name="Length", default="0")
    bpy.types.Object.fsx_xml = bpy.props.StringProperty(name="XML", default="")
    bpy.types.Object.p3d_anim_tag = bpy.props.StringProperty(name="", default="")  # Added for Ronh Code kp
    bpy.types.Object.p3d_anim_length = bpy.props.StringProperty(name="Length", default="0")  # Added for Ronh Code kp
    bpy.types.Object.p3d_xml = bpy.props.StringProperty(name="XML", default="")  # Added for Ronh Code kp

    # Bone Properties
    bpy.types.Bone.fsx_anim_tag = bpy.props.StringProperty(name="", default="")
    bpy.types.Bone.fsx_anim_length = bpy.props.StringProperty(name="Length", default="0")

    # Material definitions
    Material.fsxm_material_mode = bpy.props.EnumProperty(items=(('PBR', "PBR Material", ""), ('FSX', "Specular Material", ""), ('NONE', "Disabled", ""), ),
                                                         name="P3D/FSX Material", default='NONE', update=switch_material,)

    blendtypes = [(a, a, "") for a in ['Zero', 'One', 'SrcColor', 'InvSrcColor', 'SrcAlpha', 'InvSrcAlpha',
                                       'DestAlpha', 'InvDestAlpha', 'DestColor', 'InvDestColor']]
    emissivetypes = [(a, a, "") for a in ['AdditiveNightOnly', 'Blend', 'MultiplyBlend', 'Additive',
                                          'AdditiveNightOnlyUserControlled', 'BlendUserControlled',
                                          'AdditiveUserControlled']]
    emissivetypes_pbr = [(a, a, "") for a in ['AdditiveNightOnly', 'Additive']]
    rendermode = [(a, a, "") for a in ['Opaque', 'Masked', 'Translucent']]
    metallicsource = [(a, a, "") for a in ['MetallicAlpha', 'AlbedoAlpha']]
    ztesttypes = [(a, a, "") for a in ['Never', 'Less', 'Equal', 'LessEqual', 'Greater', 'NotEqual', 'GreaterEqual', 'Always']]

    detailblendmode = [(a, a, "") for a in ['Multiply', 'Blend']]

    # Textures
    Material.fsxm_diffusetexture = PointerProperty(type=Image, name="diffuse map", update=matchdiffuse)
    Material.fsxm_metallictexture = PointerProperty(type=Image, name="metallic map", update=matchmetallic)
    Material.fsxm_speculartexture = PointerProperty(type=Image, name="specular map", update=matchspecular)
    Material.fsxm_bumptexture = PointerProperty(type=Image, name="normal map", update=matchnormal)
    Material.fsxm_detailtexture = PointerProperty(type=Image, name="detail map", update=matchdetail)
    Material.fsxm_emissivetexture = PointerProperty(type=Image, name="emissive map", update=matchemissive)
    Material.fsxm_fresnelramp = PointerProperty(type=Image, name="fresnel ramp")
    Material.fsxm_clearcoattexture = PointerProperty(type=Image, name="clearcoat map", update=matchclearcoat)       # Dave_W

    # Material Properties
    Material.fsxm_rendermode = EnumProperty(name="Render Mode", default='Opaque', items=rendermode, update=switch_pbr_blending)
    Material.fsxm_metallicsource = EnumProperty(name="Smoothness source", default='MetallicAlpha', items=metallicsource)
    Material.fsxm_metallichasocclusion = BoolProperty(name="Metallic map has occlusion", default=True)
    Material.fsxm_metallichasreflection = BoolProperty(name="Metallic map has reflection", default=False)
    Material.fsxm_maskedthreshold = FloatProperty(name="Masked Threshold", default=0.0, min=0.0)
    Material.fsxm_alphatocoverage = BoolProperty(name="Use AlphaToCoverage", default=False)
    Material.fsxm_decalorder = IntProperty(name="Decal Order (Z-bias)", default=0, min=0, max=50)
    Material.fsxm_clearcoatcontainsnormals = BoolProperty(name="Clearcoat has normal map", default=False)    # Dave_W

    Material.fsxm_ztest = BoolProperty(name="Z-Test alpha", default=False)
    Material.fsxm_ztestmode = EnumProperty(name="Alpha test function", default='Never', items=ztesttypes)
    Material.fsxm_ztestlevel = FloatProperty(name="Alpha test level", default=0.0, min=0.0, max=255)

    Material.fsxm_allowbloom = BoolProperty(name="Allow bloom", default=False)
    Material.fsxm_emissivebloom = BoolProperty(name="Allow emissive bloom", default=False)
    Material.fsxm_ambientlightscale = FloatProperty(name="Ambient light scale", default=0.5, min=0.0, max=1.0)
    Material.fsxm_bloommaterialcopy = BoolProperty(name="Bloom material by copying", default=False)
    Material.fsxm_bloommaterialmodulatingalpha = BoolProperty(name="Bloom material modulating by alpha", default=False)
    Material.fsxm_nospecbloom = BoolProperty(name="No specular bloom", default=False)
    Material.fsxm_bloomfloor = FloatProperty(name="Specular bloom floor", default=0.9, min=0.0, max=1.0)

    Material.fsxm_emissivemode = EnumProperty(name="Mode", default='AdditiveNightOnly', items=emissivetypes)   # Emissive mode
    Material.fsxm_emissivemode_pbr = EnumProperty(name="Mode", default='AdditiveNightOnly', items=emissivetypes_pbr)

    Material.fsxm_assumevertical = BoolProperty(name="Assume vertical normal", default=False)
    Material.fsxm_blendconst = BoolProperty(name="Blend constant", default=False)
    Material.fsxm_doublesided = BoolProperty(name="Double sided", default=False)
    Material.fsxm_forceclamp = BoolProperty(name="Force texture address clamp", default=False)
    Material.fsxm_forcewrap = BoolProperty(name="Force texture address wrap", default=False)
    Material.fsxm_nobasespec = BoolProperty(name="No base material specular", default=False)
    Material.fsxm_noshadow = BoolProperty(name="No shadow", default=False)
    Material.fsxm_nozwrite = BoolProperty(name="No Z-Write", default=False)
    Material.fsxm_pverts = BoolProperty(name="Prelit vertices", default=False)
    Material.fsxm_skinned = BoolProperty(name="Skinned mesh", default=False)
    Material.fsxm_zwrite = BoolProperty(name="Z-Write alpha", default=False)
    Material.fsxm_vshadow = BoolProperty(name="Volume shadow", default=False)

    Material.fsxm_zbias = IntProperty(name="Z-Bias", default=0, min=-50, max=0, update=toggle_zbias)

    Material.fsxm_falphamult = FloatProperty(name="Final alpha multiply", default=1.0, min=0.0, max=1.0)
    Material.fsxm_falpha = BoolProperty(name="Set final alpha value at render time", default=False)

    Material.fsxm_srcblend = EnumProperty(name="Source Blend", default='One', items=blendtypes)
    Material.fsxm_destblend = EnumProperty(name="Dest Blend", default='Zero', items=blendtypes)

    Material.fsxm_fresdif = BoolProperty(name="Diffuse", default=False)
    Material.fsxm_fresref = BoolProperty(name="Environment", default=False)
    Material.fsxm_fresspec = BoolProperty(name="Specular", default=False)

    Material.fsxm_detailscale = FloatProperty(name="Detail scale", default=1, min=0, update=setDetailScale)
    Material.fsxm_bumpscale = FloatProperty(name="Bump scale", default=1, min=0, update=setBumpScale)

    Material.fsxm_precip1 = BoolProperty(name="Take into account", default=False)
    Material.fsxm_precip2 = BoolProperty(name="Apply offset to start", default=False)
    Material.fsxm_precipoffs = FloatProperty(name="Offset", min=0.0, max=1.0)

    Material.fsxm_blddif = BoolProperty(name="Blend diffuse by diffuse alpha", default=False)
    Material.fsxm_bldspec = BoolProperty(name="Blend diffuse by inverse of specular alpha", default=False)
    Material.fsxm_bledif = BoolProperty(name="Blend env by inverse of diffuse alpha", default=False)
    Material.fsxm_blespec = BoolProperty(name="Blend env by specular map alpha", default=False)
    Material.fsxm_refscale = FloatProperty(name="Reflection scale", default=0, min=0.0, max=100)    # 19/03/2023 changed name to Reflection scale to be the same as in 3DS and MCX  Dave_W
    Material.fsxm_specscale = IntProperty(name="Specular map power scale", default=64, min=0, max=256)
    Material.fsxm_globenv = BoolProperty(name="Use global environment map", default=True)
    Material.fsxm_environmentmap = PointerProperty(type=Image, name="Custom environment map", update=switch_environmentmap)

    # for PBR material. ON
    Material.fsxm_normal_scale_x = FloatProperty(name="X", default=1.0, update=setBumpScale)
    Material.fsxm_normal_scale_y = FloatProperty(name="Y", default=1.0, update=setBumpScale)
    Material.fsxm_detail_scale_x = FloatProperty(name="X", default=1.0, update=setDetailScale)
    Material.fsxm_detail_scale_y = FloatProperty(name="Y", default=1.0, update=setDetailScale)

    Material.fsxm_BumpTextureUVChannel = IntProperty(name="Normal UV Channel", default=1, min=1, max=2)
    Material.fsxm_DetailBlendMode = EnumProperty(name="Detail blend mode", default='Multiply', items=detailblendmode, update=setDetailBlend)
    Material.fsxm_DetailBlendWeight = FloatProperty(name="Detail Blend Weight", default=0.0, min=0.0, max=1000.0)
    Material.fsxm_DetailColor = FloatVectorProperty(name="DetailColor", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0))
    Material.fsxm_DetailOffsetU = FloatProperty(name="Detail offset U", default=0.0, min=0.0, max=1000.0, update=setDetailScale)
    Material.fsxm_DetailOffsetV = FloatProperty(name="Detail offset V", default=0.0, min=0.0, max=1000.0, update=setDetailScale)
    Material.fsxm_DetailRotation = FloatProperty(name="Detail rotation", default=0.0, min=-360.0, max=360.0, update=setDetailScale)
    Material.fsxm_DetailScaleV = FloatProperty(name="Detail scale V", default=1.0, min=0.0, max=64.0)
    Material.fsxm_DetailTextureUVChannel = IntProperty(name="Detail UV channel", default=1, min=1, max=2)
    Material.fsxm_DiffuseTextureUVChannel = IntProperty(name="Diffuse UV channel", default=1, min=1, max=2)
    Material.fsxm_SpecularTextureUVChannel = IntProperty(name="Specular UV channel", default=1, min=1, max=2)
    Material.fsxm_AlbedoTextureUVChannel = IntProperty(name="Albedo UV channel", default=1, min=1, max=2)
    Material.fsxm_MetallicTextureUVChannel = IntProperty(name="Metallic UV channel", default=1, min=1, max=2)
    Material.fsxm_EmissiveTextureUVChannel = IntProperty(name="Emissive UV channel", default=1, min=1, max=2)
    Material.fsxm_MaskFinalAlphaBlendByDetailBlendMask = BoolProperty(name="Mask by detail blend mask", default=False)
    Material.fsxm_MaskDiffuseBlendsByDetailBlendMask = BoolProperty(name="Mask diffuse blends by detail blend mask", default=False)
    Material.fsxm_MaterialScript = StringProperty(name="Script", subtype='FILE_PATH')
    Material.fsxm_TemperatureScale = FloatProperty(name="Temperature scale", default=1.0, min=0.0, max=10.0)
    Material.fsxm_UseDetailAlphaAsBlendMask = BoolProperty(name="Use detail alpha as blend mask", default=False)
    Material.fsxm_UseEmissiveAlphaAsHeatMap = BoolProperty(name="Use emissive map as alpha heat map", default=False)
    Material.fsxm_ClearcoatTextureUVChannel = IntProperty(name="Clearcoat UV Channel", default=1, min=1, max=2)         # Dave_W

    Material.fsxm_vcpaneltex = BoolProperty(name="Is virtual cockpit panel texture", default=False)
    Material.fsxm_nnumbertex = BoolProperty(name="Is N-Number texture", default=False)
