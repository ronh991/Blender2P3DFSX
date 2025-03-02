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
from bpy.types import Material
from bpy.props import IntProperty, BoolProperty, StringProperty, FloatProperty, EnumProperty, FloatVectorProperty
import os
from . environment import *


class FSXSetOpaque(bpy.types.Operator):
    bl_idname = "fsx.set_opaque"
    bl_label = "Set Default Opaque"
    bl_description = "Sets BLENDER Blend Method to Opaque"

    def execute(self, context):
        mat = context.active_object.active_material
        mat.fsxm_srcblend = 'One'
        mat.fsxm_destblend = 'Zero'
        mat.blend_method = 'OPAQUE'
        return {'FINISHED'}


class FSXSetTransparent(bpy.types.Operator):
    bl_idname = "fsx.set_transparent"
    bl_label = "Set Default Transparent"
    bl_description = "Sets BLENDER Blend Method to Blend"

    def execute(self, context):
        mat = context.active_object.active_material
        mat.fsxm_srcblend = 'SrcAlpha'
        mat.fsxm_destblend = 'InvSrcAlpha'
        mat.blend_method = 'BLEND'
        mat.show_transparent_back = False
        return {'FINISHED'}


class FSXMaterial(bpy.types.Panel):
    bl_label = "P3D/FSX Material Params"
    bl_idname = "FSXMATERIAL_PT_fsx_props"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}
    useP3dSDK = "False"

    def execute(self, context):
        self.useP3dSDK = bpy.types.Scene.fsx_bool_p3dSDK
        if self.useP3dSDK is True:
            self.useP3dSDK = "True"
        else:
            self.useP3dSDK = "False"
        return {'FINISHED'}

    def switch_to_pbr(self, context):
        self.report({'WARNING'}, "Switched to PBR material.")
        mat = context.active_object.active_material
        return {'FINISHED'}

    def draw(self, context):
        mat = context.active_object.active_material
        layout = self.layout

        if mat:
            box = layout.box()
            box.label(text="Material Mode", icon='MATERIAL')
            box.prop(mat, 'fsxm_material_mode', text="Select")

            if mat.fsxm_material_mode != 'NONE':
                if mat.fsxm_material_mode == 'PBR':
                    subbox = box.box()
                    subbox.label(text="PBR material only for P3D v4.4 and up.", icon='ERROR')
                    subbox = box.box()
                    subbox.label(text="Base Color", icon='TEXTURE')
                    subbox.prop(mat, 'fsxm_BaseColor')
                    subbox.prop(mat, 'fsxm_metallic_scale')
                    subbox.prop(mat, 'fsxm_smoothness_scale')
                    subbox = box.box()
                elif mat.fsxm_material_mode == 'FSX':
                    subbox = box.box()
                    subbox.label(text="Diffuse Color", icon='TEXTURE')
                    subbox.prop(mat, 'fsxm_DiffuseColor')
                    subbox.label(text="Specular Color", icon='TEXTURE')
                    subbox.prop(mat, 'fsxm_SpecularColor')
                    subbox.label(text="Specular Highlights", icon='TEXTURE')
                    subbox.prop(mat, 'fsxm_power_scale')
                    subbox = box.box()
                    subbox.label(text="Emissive Color", icon='TEXTURE') # no PBR emissive  ... yet?
                    subbox.prop(mat, 'fsxm_EmissiveColor')

                # ToDo: PBR and Specular base color - Albedo (PBR) and Diffuse(Spec FallbackDiffuse) - PBR/SPECULAR

                # ToDo: Metallic and Smoothness - PBR

                # ToDo: Emissive Color nodes - PBR/SPECULAR

                # ToDo - Done: Specular Power(has this already below - specscale), DetailScale(detailscale), BumpScale (bumpscale), EnvironmentLevelScale(refscale) - SPECULAR


                # Textures              # 28-02-2023 Rearranged to match nodes row order     Dave_W
                subbox = box.box()
                subbox.label(text="Textures", icon='TEXTURE')
                if mat.fsxm_material_mode == 'PBR':
                    subbox.label(text="Albedo:")
                elif mat.fsxm_material_mode == 'FSX':
                    subbox.label(text="Diffuse:")
                subbox.template_ID(mat, "fsxm_diffusetexture", new="image.new", open="image.open")

                if mat.fsxm_material_mode == 'PBR':
                    subbox.label(text="Metallic:")
                    subbox.template_ID(mat, "fsxm_metallictexture", new="image.new", open="image.open")
                elif mat.fsxm_material_mode == 'FSX':
                    subbox.label(text="Specular:")
                    subbox.template_ID(mat, "fsxm_speculartexture", new="image.new", open="image.open")

                subbox.label(text="Emissive/Self Illumination:")
                subbox.template_ID(mat, "fsxm_emissivetexture", new="image.new", open="image.open")

                subbox.label(text="Normal/Bump:")
                subbox.template_ID(mat, "fsxm_bumptexture", new="image.new", open="image.open")

                if mat.fsxm_material_mode == 'PBR':
                    subbox.label(text="Detail:")
                    subbox.template_ID(mat, "fsxm_detailtexture", new="image.new", open="image.open")

                if ((mat.fsxm_material_mode == 'PBR' and context.scene.global_sdk == 'p3dv5') or (mat.fsxm_material_mode == 'PBR' and context.scene.global_sdk == 'p3dv6')):             # Dave_W
                    subbox.label(text="Clearcoat:")
                    subbox.template_ID(mat, "fsxm_clearcoattexture", new="image.new", open="image.open")

                # ToDo: add this for real for v6
                # if ((mat.fsxm_material_mode == 'PBR' and context.scene.global_sdk == 'p3dv6')):             # RonH
                    # subbox.label(text="Precipitation:")
                    # subbox.template_ID(mat, "fsxm_precipitationtexture", new="image.new", open="image.open")

            if mat.fsxm_material_mode == 'PBR':
                subbox = box.box()
                subbox.label(text="Render Mode", icon='GP_MULTIFRAME_EDITING')
                subbox.prop(mat, 'fsxm_rendermode')
                subbox.prop(mat, 'fsxm_maskedthreshold')
                subbox.prop(mat, 'fsxm_alphatocoverage')

                subbox = box.box()
                subbox.label(text="Metallic properties", icon='NODE_MATERIAL')
                subbox.prop(mat, 'fsxm_metallichasocclusion')
                if ((context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):           # Dave_W
                    subbox.prop(mat, 'fsxm_metallichasreflection')
                subbox.prop(mat, 'fsxm_metallicsource')

                subbox = box.box()
                subbox.label(text="Emissive Properties", icon='OUTLINER_OB_LIGHT')
                subbox.prop(mat, 'fsxm_emissivemode_pbr')

                if ((context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):           # Dave_W
                    subbox = box.box()
                    subbox.label(text="Clearcoat Properties", icon='NODE_MATERIAL')
                    subbox.prop(mat, 'fsxm_clearcoatcontainsnormals')

                subbox = box.box()
                subbox.label(text="UV Map Channels", icon='UV')
                subbox.prop(mat, 'fsxm_AlbedoTextureUVChannel')
                subbox.prop(mat, 'fsxm_MetallicTextureUVChannel')
                subbox.prop(mat, 'fsxm_BumpTextureUVChannel')
                subbox.prop(mat, 'fsxm_EmissiveTextureUVChannel')
                subbox.prop(mat, 'fsxm_DetailTextureUVChannel')

                if ((context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):           # Dave_W
                    subbox.prop(mat, 'fsxm_ClearcoatTextureUVChannel')

                subbox = box.box()
                subbox.label(text="Normal Map", icon='MOD_NORMALEDIT')
                row = subbox.row()
                row.label(text="Scale")
                row.prop(mat, 'fsxm_normal_scale_x')
                row.prop(mat, 'fsxm_normal_scale_y')

                subbox = box.box()
                subbox.label(text="Detail Map", icon='TEXTURE')
                row = subbox.row()
                row.label(text="Scale")
                row.prop(mat, 'fsxm_detail_scale_x')
                row.prop(mat, 'fsxm_detail_scale_y')

                subbox = box.box()
                subbox.label(text="Script Properties", icon='SCRIPT')
                subbox.prop(mat, 'fsxm_MaterialScript')
                #subbox.template_ID(mat, "fsxm_MaterialScript", open="file.open")

                subbox = box.box()
                subbox.label(text="Enhanced Parameters", icon='ORIENTATION_GIMBAL')
                subbox.prop(mat, 'fsxm_assumevertical')
                subbox.prop(mat, 'fsxm_noshadow')
                subbox.prop(mat, 'fsxm_pverts')
                subbox.prop(mat, 'fsxm_doublesided')
                subbox.prop(mat, 'fsxm_decalorder')

                subbox = box.box()
                subbox.label(text="Aircraft Material Params", icon='FORCE_WIND')
                subbox.prop(mat, 'fsxm_vcpaneltex')

            elif mat.fsxm_material_mode == 'FSX':
                subbox = box.box()
                subbox.label(text="Material Alpha Test", icon='IMAGE_ALPHA')
                subbox.prop(mat, 'fsxm_ztest')
                subbox.prop(mat, 'fsxm_ztestmode')
                subbox.prop(mat, 'fsxm_ztestlevel')

                subbox = box.box()
                subbox.label(text="Final Alpha Blend", icon='IMAGE_ALPHA')
                subbox.prop(mat, 'fsxm_falphamult')
                subbox.prop(mat, 'fsxm_falpha')

                subbox = box.box()
                subbox.label(text="Bloom", icon='LIGHT_SUN')
                subbox.prop(mat, 'fsxm_allowbloom')
                subbox.prop(mat, 'fsxm_emissivebloom')
                subbox.prop(mat, 'fsxm_ambientlightscale', slider=True)
                subbox.prop(mat, 'fsxm_bloommaterialcopy')
                subbox.prop(mat, 'fsxm_bloommaterialmodulatingalpha')
                subbox.prop(mat, 'fsxm_nospecbloom')
                subbox.prop(mat, 'fsxm_bloomfloor', slider=True)

                subbox = box.box()
                subbox.label(text="Emissive Properties", icon='OUTLINER_OB_LIGHT')
                subbox.prop(mat, 'fsxm_emissivemode')

                if ((context.scene.global_sdk == 'p3dv4') or (context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):
                    subbox = box.box()
                    subbox.label(text="Script Properties", icon='SCRIPT')
                    subbox.prop(mat, 'fsxm_MaterialScript')
                    #subbox.template_ID(mat, "fsxm_MaterialScript", open="file.open")

                subbox = box.box()
                subbox.label(text="Enhanced Parameters", icon='ORIENTATION_GIMBAL')
                subbox.prop(mat, 'fsxm_assumevertical')
                subbox.prop(mat, 'fsxm_blendconst')
                subbox.prop(mat, 'fsxm_doublesided')
                subbox.prop(mat, 'fsxm_forceclamp')
                subbox.prop(mat, 'fsxm_forcewrap')
                subbox.prop(mat, 'fsxm_nobasespec')
                subbox.prop(mat, 'fsxm_noshadow')
                subbox.prop(mat, 'fsxm_nozwrite')
                if ((context.scene.global_sdk == 'p3dv2') or (context.scene.global_sdk == 'p3dv3') or (context.scene.global_sdk == 'p3dv4') or (context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):
                    subbox.prop(mat, 'fsxm_zbias')
                subbox.prop(mat, 'fsxm_pverts')
                subbox.prop(mat, 'fsxm_skinned')
                subbox.prop(mat, 'fsxm_zwrite')
                subbox.prop(mat, 'fsxm_vshadow')

                subbox = box.box()
                subbox.label(text="Framebuffer Blend", icon='GP_MULTIFRAME_EDITING')
                row = subbox.row()
                row.operator("fsx.set_opaque", text="Set Opaque")
                row.operator("fsx.set_transparent", text="Set Transparent")
                subbox.prop(mat, 'fsxm_srcblend')
                subbox.prop(mat, 'fsxm_destblend')

                subbox = box.box()
                subbox.label(text="Fresnel", icon='COLORSET_13_VEC')
                subbox.label(text="Fresnel Ramp:")
                subbox.template_ID(mat, "fsxm_fresnelramp", new="image.new", open="image.open")
                subbox.prop(mat, 'fsxm_fresdif')
                subbox.prop(mat, 'fsxm_fresref')
                subbox.prop(mat, 'fsxm_fresspec')

                if ((context.scene.global_sdk == 'p3dv4') or (context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):
                    subbox = box.box()
                    subbox.label(text="UV Map Channels", icon='UV')
                    subbox.prop(mat, 'fsxm_DiffuseTextureUVChannel')
                    subbox.prop(mat, 'fsxm_MetallicTextureUVChannel')
                    subbox.prop(mat, 'fsxm_BumpTextureUVChannel')
                    subbox.prop(mat, 'fsxm_EmissiveTextureUVChannel')
                    subbox.prop(mat, 'fsxm_DetailTextureUVChannel')

                subbox = box.box()
                subbox.label(text="Detail Texture Info", icon='TEXTURE_DATA')

                subbox.label(text="Detail:")
                subbox.template_ID(mat, "fsxm_detailtexture", new="image.new", open="image.open")

                subbox.prop(mat, 'fsxm_detailscale')
                subbox.prop(mat, 'fsxm_bumpscale')

                if ((context.scene.global_sdk == 'p3dv4') or (context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):
                    subbox.prop(mat, 'fsxm_DetailBlendMode')
                    subbox.prop(mat, 'fsxm_DetailBlendWeight')
                    subbox.prop(mat, 'fsxm_DetailColor')
                    subbox.prop(mat, 'fsxm_DetailOffsetU')
                    subbox.prop(mat, 'fsxm_DetailOffsetV')
                    #subbox.prop(mat, 'fsxm_DetailScaleU') # only a V - assume scale U is same
                    subbox.prop(mat, 'fsxm_DetailScaleV')
                    subbox.prop(mat, 'fsxm_DetailRotation')
                    subbox.prop(mat, 'fsxm_MaskFinalAlphaBlendByDetailBlendMask')
                    subbox.prop(mat, 'fsxm_MaskDiffuseBlendsByDetailBlendMask')
                    subbox.prop(mat, 'fsxm_UseDetailAlphaAsBlendMask')

                subbox = box.box()
                subbox.label(text="Other Special Texture Info", icon='TEXTURE_DATA')

                if ((context.scene.global_sdk == 'p3dv4') or (context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):
                    subbox.prop(mat, 'fsxm_TemperatureScale')
                    subbox.prop(mat, 'fsxm_UseEmissiveAlphaAsHeatMap')
                    
                subbox = box.box()
                subbox.label(text="Precipitation", icon='MOD_FLUIDSIM')
                subbox.prop(mat, 'fsxm_precipuseprecipitation')
                subbox.prop(mat, 'fsxm_precipapplyoffset')
                subbox.prop(mat, 'fsxm_precipoffs')

                subbox = box.box()
                subbox.label(text="Special Functionality", icon='EXPERIMENTAL')
                subbox.prop(mat, 'fsxm_blddif')
                subbox.prop(mat, 'fsxm_bldspec')
                subbox.prop(mat, 'fsxm_bledif')
                subbox.prop(mat, 'fsxm_blespec')
                subbox.prop(mat, 'fsxm_globenv')
                subbox.label(text="Custom environment (Reflection) map:")
                subbox.template_ID(mat, "fsxm_environmentmap", new="image.new", open="image.open")
                subbox.prop(mat, 'fsxm_refscale')
                subbox.prop(mat, 'fsxm_specscale')
                # ToDo: Environmentmapscale - already refscale (Reflection Scale in P3D SDK) - SPECULAR

                subbox = box.box()
                subbox.label(text="Aircraft Material Params", icon='FORCE_WIND')
                subbox.prop(mat, 'fsxm_vcpaneltex')
                subbox.prop(mat, 'fsxm_nnumbertex')
