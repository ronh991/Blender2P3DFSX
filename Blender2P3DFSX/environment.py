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

    # Use this function to the blender-native material settings
    def switch_material(self, context):
        # TODO confirmation needed here! No idea how... ON
        # bpy.ops.ui.msgbox('INVOKE_DEFAULT')

        mat = context.active_object.active_material
        def set_material_properties(self, context):
            print("set material")
            mat = context.active_object.active_material
            # force an update to populate shader nodes
            mat.fsxm_BaseColor = mat.fsxm_BaseColor
            mat.fsxm_DiffuseColor = mat.fsxm_DiffuseColor
            mat.fsxm_SpecularColor = mat.fsxm_SpecularColor
            mat.fsxm_EmissiveColor = mat.fsxm_EmissiveColor
            mat.fsxm_metallic_scale = mat.fsxm_metallic_scale
            mat.fsxm_smoothness_scale = mat.fsxm_smoothness_scale
            mat.fsxm_power_scale = mat.fsxm_power_scale

            # Textures
            mat.fsxm_diffusetexture = mat.fsxm_diffusetexture
            mat.fsxm_metallictexture = mat.fsxm_metallictexture
            mat.fsxm_speculartexture = mat.fsxm_speculartexture
            mat.fsxm_bumptexture = mat.fsxm_bumptexture
            mat.fsxm_detailtexture = mat.fsxm_detailtexture
            mat.fsxm_emissivetexture = mat.fsxm_emissivetexture
            mat.fsxm_fresnelramp = mat.fsxm_fresnelramp
            mat.fsxm_clearcoattexture = mat.fsxm_clearcoattexture

            # mat Properties
            mat.fsxm_rendermode = mat.fsxm_rendermode
            mat.fsxm_metallicsource = mat.fsxm_metallicsource
            mat.fsxm_metallichasocclusion = mat.fsxm_metallichasocclusion
            mat.fsxm_metallichasreflection = mat.fsxm_metallichasreflection
            mat.fsxm_maskedthreshold = mat.fsxm_maskedthreshold
            mat.fsxm_alphatocoverage = mat.fsxm_alphatocoverage
            mat.fsxm_decalorder = mat.fsxm_decalorder
            mat.fsxm_clearcoatcontainsnormals = mat.fsxm_clearcoatcontainsnormals

            mat.fsxm_ztest = mat.fsxm_ztest
            mat.fsxm_ztestmode = mat.fsxm_ztestmode
            mat.fsxm_ztestlevel = mat.fsxm_ztestlevel

            mat.fsxm_allowbloom = mat.fsxm_allowbloom
            mat.fsxm_emissivebloom = mat.fsxm_emissivebloom
            mat.fsxm_ambientlightscale = mat.fsxm_ambientlightscale
            mat.fsxm_bloommaterialcopy = mat.fsxm_bloommaterialcopy
            mat.fsxm_bloommaterialmodulatingalpha = mat.fsxm_bloommaterialmodulatingalpha
            mat.fsxm_nospecbloom = mat.fsxm_nospecbloom
            mat.fsxm_bloomfloor = mat.fsxm_bloomfloor

            mat.fsxm_emissivemode = mat.fsxm_emissivemode
            mat.fsxm_emissivemode_pbr = mat.fsxm_emissivemode_pbr

            mat.fsxm_assumevertical = mat.fsxm_assumevertical
            mat.fsxm_blendconst = mat.fsxm_blendconst
            mat.fsxm_doublesided = mat.fsxm_doublesided
            mat.fsxm_forceclamp = mat.fsxm_forceclamp
            mat.fsxm_forcewrap = mat.fsxm_forcewrap
            mat.fsxm_nobasespec = mat.fsxm_nobasespec
            mat.fsxm_noshadow = mat.fsxm_noshadow
            mat.fsxm_nozwrite = mat.fsxm_nozwrite
            mat.fsxm_pverts = mat.fsxm_pverts
            mat.fsxm_skinned = mat.fsxm_skinned
            mat.fsxm_zwrite = mat.fsxm_zwrite
            mat.fsxm_vshadow = mat.fsxm_vshadow

            mat.fsxm_zbias = mat.fsxm_zbias

            mat.fsxm_falphamult = mat.fsxm_falphamult
            mat.fsxm_falpha = mat.fsxm_falpha

            mat.fsxm_srcblend = mat.fsxm_srcblend
            mat.fsxm_destblend = mat.fsxm_destblend

            mat.fsxm_fresdif = mat.fsxm_fresdif
            mat.fsxm_fresref = mat.fsxm_fresref
            mat.fsxm_fresspec = mat.fsxm_fresspec

            mat.fsxm_detailscale = mat.fsxm_detailscale
            mat.fsxm_bumpscale = mat.fsxm_bumpscale

            mat.fsxm_precipuseprecipitation = mat.fsxm_precipuseprecipitation
            mat.fsxm_precipapplyoffset = mat.fsxm_precipapplyoffset
            mat.fsxm_precipoffs = mat.fsxm_precipoffs

            mat.fsxm_blddif = mat.fsxm_blddif
            mat.fsxm_bldspec = mat.fsxm_bldspec
            mat.fsxm_bledif = mat.fsxm_bledif
            mat.fsxm_blespec = mat.fsxm_blespec
            mat.fsxm_refscale = mat.fsxm_refscale
            mat.fsxm_specscale = mat.fsxm_specscale
            mat.fsxm_globenv = mat.fsxm_globenv
            mat.fsxm_environmentmap = mat.fsxm_environmentmap

            # for PBR mat. ON
            mat.fsxm_normal_scale_x = mat.fsxm_normal_scale_x
            mat.fsxm_normal_scale_y = mat.fsxm_normal_scale_y
            mat.fsxm_detail_scale_x = mat.fsxm_detail_scale_x
            mat.fsxm_detail_scale_y = mat.fsxm_detail_scale_y

            mat.fsxm_BumpTextureUVChannel = mat.fsxm_BumpTextureUVChannel
            mat.fsxm_DetailBlendMode = mat.fsxm_DetailBlendMode
            mat.fsxm_DetailBlendWeight = mat.fsxm_DetailBlendWeight
            mat.fsxm_DetailColor = mat.fsxm_DetailColor
            mat.fsxm_DetailOffsetU = mat.fsxm_DetailOffsetU
            mat.fsxm_DetailOffsetV = mat.fsxm_DetailOffsetV
            mat.fsxm_DetailRotation = mat.fsxm_DetailRotation
            mat.fsxm_DetailScaleV = mat.fsxm_DetailScaleV
            mat.fsxm_DetailTextureUVChannel = mat.fsxm_DetailTextureUVChannel
            mat.fsxm_DiffuseTextureUVChannel = mat.fsxm_DiffuseTextureUVChannel
            mat.fsxm_SpecularTextureUVChannel = mat.fsxm_SpecularTextureUVChannel
            mat.fsxm_AlbedoTextureUVChannel = mat.fsxm_AlbedoTextureUVChannel
            mat.fsxm_MetallicTextureUVChannel = mat.fsxm_MetallicTextureUVChannel
            mat.fsxm_EmissiveTextureUVChannel = mat.fsxm_EmissiveTextureUVChannel
            mat.fsxm_MaskFinalAlphaBlendByDetailBlendMask = mat.fsxm_MaskFinalAlphaBlendByDetailBlendMask
            mat.fsxm_MaskDiffuseBlendsByDetailBlendMask = mat.fsxm_MaskDiffuseBlendsByDetailBlendMask
            mat.fsxm_MaterialScript = mat.fsxm_MaterialScript
            mat.fsxm_TemperatureScale = mat.fsxm_TemperatureScale
            mat.fsxm_UseDetailAlphaAsBlendMask = mat.fsxm_UseDetailAlphaAsBlendMask
            mat.fsxm_UseEmissiveAlphaAsHeatMap = mat.fsxm_UseEmissiveAlphaAsHeatMap
            mat.fsxm_ClearcoatTextureUVChannel = mat.fsxm_ClearcoatTextureUVChannel

            mat.fsxm_vcpaneltex = mat.fsxm_vcpaneltex
            mat.fsxm_nnumbertex = mat.fsxm_nnumbertex

        def reset_material_properties(self, context):
            mat = context.active_object.active_material
            mat.fsxm_BaseColor = (1.0, 1.0, 1.0, 1.0)
            mat.fsxm_DiffuseColor = (1.0, 1.0, 1.0, 1.0)
            mat.fsxm_SpecularColor = (1.0, 1.0, 1.0, 1.0)
            mat.fsxm_EmissiveColor = (0.0, 0.0, 0.0, 1.0)
            mat.fsxm_metallic_scale = 0
            mat.fsxm_smoothness_scale = 1
            mat.fsxm_power_scale = 50

            # Textures
            mat.fsxm_diffusetexture = None
            mat.fsxm_metallictexture = None
            mat.fsxm_speculartexture = None
            mat.fsxm_bumptexture = None
            mat.fsxm_detailtexture = None
            mat.fsxm_emissivetexture = None
            mat.fsxm_fresnelramp = None
            mat.fsxm_clearcoattexture = None

            # mat Properties
            mat.fsxm_rendermode = 'Opaque'
            mat.fsxm_metallicsource = 'MetallicAlpha'
            mat.fsxm_metallichasocclusion = True
            mat.fsxm_metallichasreflection = False
            mat.fsxm_maskedthreshold = 0.0
            mat.fsxm_alphatocoverage = False
            mat.fsxm_decalorder = 0
            mat.fsxm_clearcoatcontainsnormals = False

            mat.fsxm_ztest = False
            mat.fsxm_ztestmode = 'Never'
            mat.fsxm_ztestlevel = 0.0

            mat.fsxm_allowbloom = False
            mat.fsxm_emissivebloom = False
            mat.fsxm_ambientlightscale = 1.0
            mat.fsxm_bloommaterialcopy = False
            mat.fsxm_bloommaterialmodulatingalpha = False
            mat.fsxm_nospecbloom = False
            mat.fsxm_bloomfloor = 0.9

            mat.fsxm_emissivemode = 'AdditiveNightOnly'
            mat.fsxm_emissivemode_pbr = 'AdditiveNightOnly'

            mat.fsxm_assumevertical = False
            mat.fsxm_blendconst = False
            mat.fsxm_doublesided = False
            mat.fsxm_forceclamp = False
            mat.fsxm_forcewrap = False
            mat.fsxm_nobasespec = False
            mat.fsxm_noshadow = False
            mat.fsxm_nozwrite = False
            mat.fsxm_pverts = False
            mat.fsxm_skinned = False
            mat.fsxm_zwrite = False
            mat.fsxm_vshadow = False

            mat.fsxm_zbias = 0

            mat.fsxm_falphamult = 255.0
            mat.fsxm_falpha = False

            mat.fsxm_srcblend = 'One'
            mat.fsxm_destblend = 'Zero'

            mat.fsxm_fresdif = False
            mat.fsxm_fresref = False
            mat.fsxm_fresspec = False

            mat.fsxm_detailscale = 1.0
            mat.fsxm_bumpscale = 1.0

            mat.fsxm_precipuseprecipitation = False
            mat.fsxm_precipapplyoffset = False
            mat.fsxm_precipoffs = 0.0

            mat.fsxm_blddif = False
            mat.fsxm_bldspec = False
            mat.fsxm_bledif = False
            mat.fsxm_blespec = False
            mat.fsxm_refscale = 0   # 19/03/2023 changed name to Reflection scale to be the same as in 3DS and MCX  Dave_W
            mat.fsxm_specscale = 64
            mat.fsxm_globenv = True
            mat.fsxm_environmentmap = None

            # for PBR mat. ON
            mat.fsxm_normal_scale_x = 1.0
            mat.fsxm_normal_scale_y = 1.0
            mat.fsxm_detail_scale_x = 1.0
            mat.fsxm_detail_scale_y = 1.0

            mat.fsxm_BumpTextureUVChannel = 1
            mat.fsxm_DetailBlendMode = 'Multiply'
            mat.fsxm_DetailBlendWeight = 0.0
            mat.fsxm_DetailColor = (1.0, 1.0, 1.0, 1.0)
            mat.fsxm_DetailOffsetU = 0.0
            mat.fsxm_DetailOffsetV = 0.0
            mat.fsxm_DetailRotation = 0.0
            mat.fsxm_DetailScaleV = 1.0
            mat.fsxm_DetailTextureUVChannel = 1
            mat.fsxm_DiffuseTextureUVChannel = 1
            mat.fsxm_SpecularTextureUVChannel = 1
            mat.fsxm_AlbedoTextureUVChannel = 1
            mat.fsxm_MetallicTextureUVChannel = 1
            mat.fsxm_EmissiveTextureUVChannel = 1
            mat.fsxm_MaskFinalAlphaBlendByDetailBlendMask = False
            mat.fsxm_MaskDiffuseBlendsByDetailBlendMask = False
            mat.fsxm_MaterialScript = ""
            mat.fsxm_TemperatureScale = 1.0
            mat.fsxm_UseDetailAlphaAsBlendMask = False
            mat.fsxm_UseEmissiveAlphaAsHeatMap = False
            mat.fsxm_ClearcoatTextureUVChannel = 1

            mat.fsxm_vcpaneltex = False
            mat.fsxm_nnumbertex = False

        if mat.fsxm_material_mode == 'PBR':
            MaterialUtil.CreatePBRShader(mat)
            set_material_properties(self, context)
            print("Switched to PBR material.")
        elif mat.fsxm_material_mode == 'FSX':
            MaterialUtil.CreateSpecShader(mat)
            set_material_properties(self, context)
            print("Switched to specular material.")
        else:
            for n in mat.node_tree.nodes:
                mat.node_tree.nodes.remove(n)
            reset_material_properties(self, context)
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
        elif mat.fsxm_rendermode == 'Additive':
            MaterialUtil.MakeAdditive(mat)

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

    # def setMetallicScale(self, context):
        # mat = context.active_object.active_material
        # try:
            # if mat.fsxm_material_mode == 'PBR':
                # mat.node_tree.nodes["Metallic Scale"].inputs["Value"].default_value[0] = mat.fsxm_metallic_scale
        # except:
            # pass

    # def setSmoothnessScale(self, context):
        # mat = context.active_object.active_material
        # try:
            # if mat.fsxm_material_mode == 'PBR':
                # mat.node_tree.nodes["Smoothness Scale"].inputs["Value"].default_value[0] = mat.fsxm_smoothness_scale
        # except:
            # pass

    def setPowerScale(self, context):
        mat = context.active_object.active_material
        try:
            if mat.fsxm_material_mode == 'FSX':
                mat.node_tree.nodes["Power Scale"].inputs["Value"].default_value[0] = mat.fsxm_power_scale
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

    def setBaseColor(self, context):
        # PBR
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Base Color", None) is not None:
            mat.node_tree.nodes["Base Color"].outputs[0].default_value = mat.fsxm_BaseColor
        # Alpha too
        if mat.node_tree.nodes.get("Alpha Value", None) is not None:
            mat.node_tree.nodes["Alpha Value"].outputs[0].default_value = mat.fsxm_BaseColor[3]
        
    def setEmissiveColor(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Principled BSDF", None) is not None:
            mat.node_tree.nodes["Principled BSDF"].inputs["Emission"].default_value = mat.fsxm_EmissiveColor
            return
        if mat.node_tree.nodes.get("Specular BSDF", None) is not None:
            mat.node_tree.nodes["Specular BSDF"].inputs["Emissive Color"].default_value = mat.fsxm_EmissiveColor
            mat.node_tree.nodes["Emissive Color"].outputs[0].default_value = mat.fsxm_EmissiveColor

    def setDiffuseColor(self, context):
        # Specular
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Diffuse Color", None) is not None:
            mat.node_tree.nodes["Diffuse Color"].outputs[0].default_value = mat.fsxm_DiffuseColor
        # Alpha too
        if mat.node_tree.nodes.get("Alpha Value", None) is not None:
            mat.node_tree.nodes["Alpha Value"].outputs[0].default_value = mat.fsxm_DiffuseColor[3]

    def setSpecularColor(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Specular Color", None) is not None:
            mat.node_tree.nodes["Specular Color"].outputs[0].default_value = mat.fsxm_SpecularColor

    def setMetallicScale(self, context):
        # PBR
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Metallic Factor", None) is not None:
            mat.node_tree.nodes["Metallic Factor"].outputs[0].default_value = mat.fsxm_metallic_scale

    def setSmoothnessFactor(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Smoothness Factor", None) is not None:
            mat.node_tree.nodes["Smoothness Factor"].outputs[0].default_value = mat.fsxm_smoothness_scale

    def setPowerScale(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Power Factor", None) is not None:
            mat.node_tree.nodes["Power Factor"].outputs[0].default_value = mat.fsxm_power_scale

    def matchdiffuse(self, context):
        # ToDo: add in links required for diffuse (albedo specular) texture
        mat = context.active_object.active_material
        print("MatchDiffuse", mat.fsxm_material_mode)
        if mat.fsxm_material_mode == 'NONE':
            return
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        scale_diffuse = 1
        scale_detail = 1
        if mat.fsxm_diffusetexture is not None:
            if mat.fsxm_diffusetexture.name.split(".")[len(mat.fsxm_diffusetexture.name.split(".")) - 1] == 'dds':
                scale_diffuse = -1
        if mat.fsxm_detailtexture is not None:
            if mat.fsxm_detailtexture.name.split(".")[len(mat.fsxm_detailtexture.name.split(".")) - 1] == 'dds':
                scale_detail = -1
        if mat.fsxm_diffusetexture is None and mat.fsxm_detailtexture is None:
            mat.node_tree.nodes["Detail"].image = mat.fsxm_detailtexture
            if mat.fsxm_material_mode == 'PBR':
                mat.node_tree.nodes["Albedo"].image = mat.fsxm_diffusetexture
                links.new(nodes["Base Color Mix"].outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
                if nodes["Albedo"].outputs["Alpha"].links is not None:
                    for l in nodes["Albedo"].outputs["Alpha"].links:
                        print("Alpha links", nodes["Albedo"].outputs["Alpha"].links, l)
                        if l.to_socket == nodes["Principled BSDF"].inputs["Alpha"]:
                            links.remove(l)
            elif mat.fsxm_material_mode == 'FSX':
                mat.node_tree.nodes["Diffuse"].image = mat.fsxm_diffusetexture
                links.new(nodes["Diffuse Color Blend"].outputs["Color"], nodes["Specular BSDF"].inputs["Base Color"])
                if nodes["Transparency"].outputs["Color"].links is not None:
                    for l in nodes["Transparency"].outputs["Color"].links:
                        print("Transparency links", nodes["Transparency"].outputs["Color"].links, l)
                        if l.to_socket == nodes["Specular BSDF"].inputs["Transparency"]:
                            links.remove(l)

        if mat.fsxm_diffusetexture is not None and mat.fsxm_detailtexture is None:
            mat.node_tree.nodes["Detail"].image = mat.fsxm_detailtexture
            if mat.fsxm_material_mode == 'PBR':
                mat.node_tree.nodes["Albedo"].image = mat.fsxm_diffusetexture
                links.new(nodes["Albedo"].outputs["Color"], nodes["Base Color Mix"].inputs["Color1"])
                links.new(nodes["Base Color Mix"].outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
                links.new(nodes["Albedo"].outputs["Alpha"], nodes["Principled BSDF"].inputs["Alpha"])
                mat.node_tree.nodes["Albedo"].texture_mapping.scale[1] = scale_diffuse
            elif  mat.fsxm_material_mode == 'FSX':
                mat.node_tree.nodes["Diffuse"].image = mat.fsxm_diffusetexture
                links.new(nodes["Diffuse"].outputs["Color"], nodes["Diffuse Color Blend"].inputs["Color2"])
                links.new(nodes["Transparency"].outputs["Color"], nodes["Specular BSDF"].inputs["Transparency"])
                mat.node_tree.nodes["Diffuse"].texture_mapping.scale[1] = scale_diffuse

        if mat.fsxm_diffusetexture is not None and mat.fsxm_detailtexture is not None:
            mat.node_tree.nodes["Detail"].image = mat.fsxm_detailtexture
            mat.node_tree.nodes["Detail"].texture_mapping.scale[1] = scale_detail
            if mat.fsxm_material_mode == 'PBR':
                mat.node_tree.nodes["Albedo"].image = mat.fsxm_diffusetexture
                links.new(nodes["Albedo"].outputs["Color"], nodes["Base Color Mix"].inputs["Color1"])
                links.new(nodes["Detail Blend"].outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
                links.new(nodes["Albedo"].outputs["Alpha"], nodes["Principled BSDF"].inputs["Alpha"])
                mat.node_tree.nodes["Albedo"].texture_mapping.scale[1] = scale_diffuse
            elif  mat.fsxm_material_mode == 'FSX':
                mat.node_tree.nodes["Diffuse"].image = mat.fsxm_diffusetexture
                links.new(nodes["Diffuse"].outputs["Color"], nodes["Diffuse Color Blend"].inputs["Color2"])
                links.new(nodes["Diffuse Color Blend"].outputs["Color"], nodes["Detail Blend"].inputs["Color1"])
                links.new(nodes["Transparency"].outputs["Color"], nodes["Specular BSDF"].inputs["Transparency"])
                mat.node_tree.nodes["Diffuse"].texture_mapping.scale[1] = scale_diffuse

    def matchnormal(self, context):
        mat = context.active_object.active_material
        print("MatchNormal", mat.fsxm_material_mode)
        if mat.fsxm_material_mode == 'NONE':
            return
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        scale = 1
        fac = 0
        strength = 1
        if mat.fsxm_bumptexture is not None:
            if mat.fsxm_bumptexture.name.split(".")[len(mat.fsxm_bumptexture.name.split(".")) - 1] == 'dds':
                scale = -1
                fac = 1

        if mat.node_tree.nodes.get("Normal", None) is not None:
            mat.node_tree.nodes["Normal"].image = mat.fsxm_bumptexture
            if mat.fsxm_bumptexture is None:
                if nodes["Normal Map"].outputs["Normal"].links is not None:
                    for l in nodes["Normal Map"].outputs["Normal"].links:
                        print("Normal Map links", nodes["Normal Map"].outputs["Normal"].links, l)
                        if mat.fsxm_material_mode == 'FSX':
                            if l.to_socket == nodes["Specular BSDF"].inputs["Normal"]:
                                links.remove(l)
                        if mat.fsxm_material_mode == 'PBR':
                            if l.to_socket == nodes["Principled BSDF"].inputs["Normal"]:
                                links.remove(l)

            if mat.fsxm_bumptexture is not None:
                mat.node_tree.nodes["Normal"].texture_mapping.scale[1] = scale
                mat.node_tree.nodes["Normal"].image.colorspace_settings.name = 'Non-Color'
                if mat.node_tree.nodes.get("Mix Normals", None) is not None:
                    mat.node_tree.nodes["Mix Normals"].inputs["Fac"].default_value = fac
                if mat.node_tree.nodes.get("Normal Map", None) is not None:
                    mat.node_tree.nodes["Normal Map"].inputs["Strength"].default_value = strength
                if mat.fsxm_material_mode == 'FSX':
                    links.new(nodes["Normal Map"].outputs["Normal"], nodes["Specular BSDF"].inputs["Normal"])
                if mat.fsxm_material_mode == 'PBR':
                    links.new(nodes["Normal Map"].outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"])

    def matchmetallic(self, context):
        mat = context.active_object.active_material
        print("MatchMetallic", mat.fsxm_material_mode)
        if mat.fsxm_material_mode == 'NONE':
            return
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        scale = 1
        if mat.fsxm_metallictexture is not None:
            if mat.fsxm_metallictexture.name.split(".")[len(mat.fsxm_metallictexture.name.split(".")) - 1] == 'dds':
                scale = -1

        if mat.node_tree.nodes.get("Metallic", None) is not None:
            mat.node_tree.nodes["Metallic"].image = mat.fsxm_metallictexture
            oneminus_node = mat.node_tree.nodes.get("Invert 1 minus")
            if mat.fsxm_metallictexture is None:
                metallicfactor_node = mat.node_tree.nodes.get("Metallic Factor")
                smoothnessfactor_node = mat.node_tree.nodes.get("Smoothness Factor")
                links.new(metallicfactor_node.outputs[0], nodes["Principled BSDF"].inputs["Metallic"])
                links.new(smoothnessfactor_node.outputs[0], oneminus_node.inputs[1])

            elif mat.fsxm_metallictexture is not None:
                mat.node_tree.nodes["Metallic"].image.colorspace_settings.name = 'Non-Color'
                mat.node_tree.nodes["Metallic"].texture_mapping.scale[1] = scale
                separatered_node = mat.node_tree.nodes.get("Separate Red")
                links.new(nodes["Metallic"].outputs["Alpha"], oneminus_node.inputs[1])
                links.new(separatered_node.outputs["R"], nodes["Principled BSDF"].inputs["Metallic"])
                # ToDo: add in links required for metallic and smoothness texture

    def matchspecular(self, context):
        mat = context.active_object.active_material
        print("MatchSpecular", mat.fsxm_material_mode)
        if mat.fsxm_material_mode == 'NONE':
            return
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        scale = 1
        if mat.fsxm_speculartexture is not None:
            if mat.fsxm_speculartexture.name.split(".")[len(mat.fsxm_speculartexture.name.split(".")) - 1] == 'dds':
                scale = -1

        if mat.node_tree.nodes.get("specular", None) is not None:       # "specular" must not be capitalized like other node names. See line 132 func_material.py   Dave_W
            mat.node_tree.nodes["specular"].image = mat.fsxm_speculartexture
            if mat.fsxm_speculartexture is None:
                if nodes["specular"].outputs["Color"].links is not None:
                    for l in nodes["specular"].outputs["Color"].links:
                        print("Specular links", nodes["specular"].outputs["Color"].links, l)
                        if l.to_socket == nodes["Specular Color Blend"].inputs["Color2"]:
                            links.remove(l)
            if mat.fsxm_speculartexture is not None:
                mat.node_tree.nodes["specular"].texture_mapping.scale[1] = scale
                links.new(nodes["specular"].outputs["Color"], nodes["Specular Color Blend"].inputs["Color2"])
                # ToDo: add in links required for specular texture, specular color, level, glosiness, power (soften)

    def matchdetail(self, context):
        # not used see matchdiffuse
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
        print("MatchEmissive", mat.fsxm_material_mode)
        if mat.fsxm_material_mode == 'NONE':
            return
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        scale = 1
        if mat.fsxm_emissivetexture is not None:
            if mat.fsxm_emissivetexture.name.split(".")[len(mat.fsxm_emissivetexture.name.split(".")) - 1] == 'dds':
                scale = -1

        if mat.node_tree.nodes.get("Emissive", None) is not None:
            mat.node_tree.nodes["Emissive"].image = mat.fsxm_emissivetexture
            if mat.fsxm_emissivetexture is None:
                if nodes["Emissive"].outputs["Color"].links is not None:
                    for l in nodes["Emissive"].outputs["Color"].links:
                        print("Emissive links", nodes["Emissive"].outputs["Color"].links, l)
                        if mat.fsxm_material_mode == 'FSX':
                            if l.to_socket == nodes["Specular Color Blend"].inputs["Color2"]:
                                links.remove(l)

                        if mat.fsxm_material_mode == 'PBR':
                            if l.to_socket == nodes["Principled BSDF"].inputs["Emission"]:
                                links.remove(l)
            elif mat.fsxm_emissivetexture is not None:
                mat.node_tree.nodes["Emissive"].texture_mapping.scale[1] = scale
                if mat.fsxm_material_mode == 'FSX':
                    links.new(mat.node_tree.nodes["Emissive"].outputs["Color"], nodes["Emissive Color Blend"].inputs["Color2"])
                if mat.fsxm_material_mode == 'PBR':
                    links.new(mat.node_tree.nodes["Emissive"].outputs["Color"], nodes["Principled BSDF"].inputs["Emission"])

    # copied and edited from matchmetallic       Dave_W
    def matchclearcoat(self, context):
        mat = context.active_object.active_material

        if mat.node_tree.nodes.get("Clearcoat", None) is not None:
            mat.node_tree.nodes["Clearcoat"].image = mat.fsxm_clearcoattexture
            if mat.fsxm_clearcoattexture is not None:
                mat.node_tree.nodes["Clearcoat"].image.colorspace_settings.name = 'Non-Color'
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
    bpy.types.Object.fsx_anim_tag = bpy.props.StringProperty(name="FSX Animation", default="")
    bpy.types.Object.fsx_anim_length = bpy.props.StringProperty(name="Length", default="0")
    bpy.types.Object.fsx_xml = bpy.props.StringProperty(name="XML", default="")
    bpy.types.Object.p3d_anim_tag = bpy.props.StringProperty(name="P3D Animation", default="")  # Added for Ronh Code kp
    bpy.types.Object.p3d_anim_length = bpy.props.StringProperty(name="Length", default="0")  # Added for Ronh Code kp
    bpy.types.Object.p3d_xml = bpy.props.StringProperty(name="XML", default="")  # Added for Ronh Code kp

    # Bone Properties
    bpy.types.Bone.fsx_anim_tag = bpy.props.StringProperty(name="FSX Bone Anim", default="")
    bpy.types.Bone.fsx_anim_length = bpy.props.StringProperty(name="Length", default="0")

    # Material definitions
    Material.fsxm_material_mode = bpy.props.EnumProperty(items=(('PBR', "PBR Material", ""), ('FSX', "Specular Material", ""), ('NONE', "Disabled", ""), ),
                                                         name="P3D/FSX Material", default='NONE', update=switch_material,)

    blendtypes = [(a, a, "") for a in ['Zero', 'One', 'SrcColor', 'InvSrcColor', 'SrcAlpha', 'InvSrcAlpha',
                                       'DestAlpha', 'InvDestAlpha', 'DestColor', 'InvDestColor']]
    # per SDK - 4 then same 4 with 'UserControlled'
    emissivetypes = [(a, a, "") for a in ['AdditiveNightOnly', 'Blend', 'MultiplyBlend', 'Additive',
                                          'AdditiveNightOnlyUserControlled', 'BlendUserControlled','MultiplyBlendUserControlled','AdditiveUserControlled']]
    emissivetypes_pbr = [(a, a, "") for a in ['AdditiveNightOnly', 'Additive']]
    rendermode = [(a, a, "") for a in ['Opaque', 'Masked', 'Translucent', 'Additive']]
    metallicsource = [(a, a, "") for a in ['MetallicAlpha', 'AlbedoAlpha']]
    ztesttypes = [(a, a, "") for a in ['Never', 'Less', 'Equal', 'LessEqual', 'Greater', 'NotEqual', 'GreaterEqual', 'Always']]

    detailblendmode = [(a, a, "") for a in ['Multiply', 'Blend']]

    # need color PBR Albedo (base color) and SPECULAR fallbackdiffuse and specular color
    # need PBR metallic scale, smoothness scale (1 - roughness)
    # need Specular Level - is Power, Glossiness - not used??, soften - not used?? - have no idea - see P3D SDK 3DS Max

    Material.fsxm_BaseColor = FloatVectorProperty(name="BaseColor", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0), update=setBaseColor)
    Material.fsxm_DiffuseColor = FloatVectorProperty(name="DiffuseColor", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0), update=setDiffuseColor)
    Material.fsxm_SpecularColor = FloatVectorProperty(name="SpecularColor", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0), update=setSpecularColor)
    Material.fsxm_EmissiveColor = FloatVectorProperty(name="EmissiveColor", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.0, 0.0, 0.0, 1.0), update=setEmissiveColor)
    Material.fsxm_metallic_scale = FloatProperty(name="Metallic_scale", default=0, min=0, max=1.0, update=setMetallicScale)
    Material.fsxm_smoothness_scale = FloatProperty(name="Smoothness_scale", default=1, min=0, max=1.0, update=setSmoothnessFactor)
    Material.fsxm_power_scale = FloatProperty(name="Specular Level (Power scale)", default=1, min=0, max=100, update=setPowerScale)

    # Textures
    Material.fsxm_diffusetexture = PointerProperty(type=Image, name="diffuse map", update=matchdiffuse)
    Material.fsxm_metallictexture = PointerProperty(type=Image, name="metallic map", update=matchmetallic)
    Material.fsxm_speculartexture = PointerProperty(type=Image, name="specular map", update=matchspecular)
    Material.fsxm_bumptexture = PointerProperty(type=Image, name="normal map", update=matchnormal)
    Material.fsxm_detailtexture = PointerProperty(type=Image, name="detail map", update=matchdiffuse)
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

    Material.fsxm_falphamult = FloatProperty(name="Final alpha multiply", default=255.0, min=0.0, max=255.0)
    Material.fsxm_falpha = BoolProperty(name="Set final alpha value at render time", default=False)

    Material.fsxm_allowbloom = BoolProperty(name="Allow bloom", default=False)
    Material.fsxm_emissivebloom = BoolProperty(name="Allow emissive bloom", default=False)
    Material.fsxm_ambientlightscale = FloatProperty(name="Ambient light scale", default=1.0, min=0.0, max=1.0)
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

    Material.fsxm_srcblend = EnumProperty(name="Source Blend", default='One', items=blendtypes)
    Material.fsxm_destblend = EnumProperty(name="Dest Blend", default='Zero', items=blendtypes)

    Material.fsxm_fresdif = BoolProperty(name="Diffuse", default=False)
    Material.fsxm_fresref = BoolProperty(name="Reflection", default=False)
    Material.fsxm_fresspec = BoolProperty(name="Specular", default=False)

    Material.fsxm_detailscale = FloatProperty(name="Detail scale", default=1, min=0, update=setDetailScale)
    Material.fsxm_bumpscale = FloatProperty(name="Bump scale", default=1, min=0, update=setBumpScale)

    Material.fsxm_precipuseprecipitation = BoolProperty(name="Take into account", default=False)
    Material.fsxm_precipapplyoffset = BoolProperty(name="Apply offset to start", default=False)
    Material.fsxm_precipoffs = FloatProperty(name="Offset", min=0.0, max=1.0)

    Material.fsxm_blddif = BoolProperty(name="Blend diffuse by diffuse alpha", default=False)
    Material.fsxm_bldspec = BoolProperty(name="Blend diffuse by inverse of specular alpha", default=False)
    Material.fsxm_bledif = BoolProperty(name="Blend env by inverse of diffuse alpha", default=False)
    Material.fsxm_blespec = BoolProperty(name="Blend env by specular map alpha", default=False)
    Material.fsxm_refscale = FloatProperty(name="Reflection scale", default=0, min=0.0, max=100)    # 19/03/2023 changed name to Reflection scale to be the same as in 3DS and MCX  Dave_W
    Material.fsxm_specscale = IntProperty(name="Specular map power scale", default=64, min=0, max=255)
    Material.fsxm_environmentmap = PointerProperty(type=Image, name="Custom environment map", update=switch_environmentmap)
    Material.fsxm_globenv = BoolProperty(name="Use global environment map", default=False)

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
    Material.fsxm_MaterialScript = StringProperty(name="Script", subtype='FILE_PATH', description="Path converted to Filename of script file")
    #Material.fsxm_MaterialScript = PointerProperty(type=File, name="script file", description="Filename of script file")
    Material.fsxm_TemperatureScale = FloatProperty(name="Temperature scale", default=1.0, min=0.0, max=10.0)
    Material.fsxm_UseDetailAlphaAsBlendMask = BoolProperty(name="Use detail alpha as blend mask", default=False)
    Material.fsxm_UseEmissiveAlphaAsHeatMap = BoolProperty(name="Use emissive map as alpha heat map", default=False)
    Material.fsxm_ClearcoatTextureUVChannel = IntProperty(name="Clearcoat UV Channel", default=1, min=1, max=2)         # Dave_W

    Material.fsxm_vcpaneltex = BoolProperty(name="Is virtual cockpit panel texture", default=False)
    Material.fsxm_nnumbertex = BoolProperty(name="Is N-Number texture", default=False)
