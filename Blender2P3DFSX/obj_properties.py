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
from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, REG_SZ, REG_EXPAND_SZ
import xml.etree.ElementTree as etree
from . environment import *
from . func_animation import FSXClearAnim
from . func_attachpoint import FSXClearAttach


class FSXBoneProps(bpy.types.Panel):
    bl_label = "P3D/FSX Properties"
    bl_idname = "BONE_PT_fsx_props"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        if bpy.context.mode != "POSE":
            box.label(text="Animation tags are stored in individual bones - pose mode.", icon='ANIM')
        else:
            box.label(text="Animation Tag:", icon='ANIM')
            row = box.row()
            row.prop(bpy.context.active_bone, "fsx_anim_tag", text="Anim tag")
            row.prop(bpy.context.active_bone, "fsx_anim_length", text="Anim length")
            box.operator("fsx.anim_clear")


class FSXObjectProps(bpy.types.Panel):
    bl_label = "P3D/FSX Properties"
    bl_idname = "OBJECT_PT_fsx_props"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        if bpy.context.active_object.type == 'ARMATURE':
            layout = self.layout
            box = layout.box()
            box.label(text="Animation tags are stored in individual bones.", icon='ANIM')
        else:
            layout = self.layout
            box = layout.box()
            box.label(text="Animation Tag", icon='ANIM')
            subbox = box.box()
            row = subbox.row()
            row.prop(bpy.context.active_object, "fsx_anim_tag", text="Anim tag")
            row.prop(bpy.context.active_object, "fsx_anim_length", text="Anim length")
            subbox.row().separator()
            subbox.operator('fsx.anim_clear', icon='TRASH')

            box = layout.box()
            box.label(text="Attach Point Tag", icon='HOOK')
            if context.active_object.fsx_xml != "":
                subbox = box.box()
                root = etree.fromstring(context.active_object.fsx_xml)
                attachpt = root.find("Attachpoint")
                if attachpt is not None:
                    subbox.label(text="Name: %s" %attachpt.get("name")[9:])
                    row = subbox.row()
                    effect = root.find(".//Effect")
                    if effect is not None:
                        row = subbox.row()
                        row.label(text="Effect: %s" %effect.get("effectName"), icon='SHADERFX')
                        params = effect.get("effectParams")
                        if params != '':
                            subrow = row.row()
                            subrow.label(text="Params: %s" %params)
                    subbox.row().separator()
                visibility = root.find("Visibility")
                if visibility is not None:
                    subrow = subbox.row()
                    subrow.label(text="Visibility: %s" %visibility.get("name"), icon='HIDE_OFF')
                    subbox.row().separator()
                mouserect = root.find("MouseRect")
                if mouserect is not None:
                    subrow = subbox.row()
                    subrow.label(text="MouseRect: %s" %mouserect.get("name"), icon='MOUSE_MOVE')
                    subbox.row().separator()
                platform = root.find("Platform")
                if platform is not None:
                    subrow = subbox.row()
                    subrow.label(text="Platform type: %s" %platform.get("surfaceType"), icon='OUTLINER_OB_SURFACE')
                    subbox.row().separator()
                nocrash = root.find("NoCrash")
                if nocrash is not None:
                    subrow = subbox.row()
                    subrow.label(text="NoCrash", icon='IPO_BOUNCE')
                    subbox.row().separator()
                subbox.operator('fsx.attach_clear', icon='TRASH')
