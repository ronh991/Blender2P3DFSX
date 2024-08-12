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
import xml.etree.ElementTree as etree
import struct
from mathutils import Vector
import os
from os import urandom
from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, REG_SZ, REG_EXPAND_SZ


class FindSDK(bpy.types.Operator):
    bl_idname = "fsx.sdk_find"
    bl_label = "Manually Find SDK"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        bpy.context.scene.fsx_sdkpath = os.path.dirname(self.filepath)
        if bpy.context.scene.global_sdk == 'fsx':
            bpy.context.scene.fsx_modeldefpath = ''.join([bpy.context.scene.fsx_sdkpath, "Environment Kit\\Modeling SDK\\bin\\modeldef.xml"])
        elif bpy.context.scene.global_sdk == 'p3dv1':
            bpy.context.scene.fsx_modeldefpath = ''.join([bpy.context.scene.fsx_sdkpath, "\\Environment Kit\\Modeling SDK\\bin\\modeldef.xml"])
        elif context.scene.global_sdk == 'p3dv2':
            bpy.context.scene.fsx_modeldefpath = ''.join([bpy.context.scene.fsx_sdkpath, "\\Modeling SDK\\bin\\modeldef.xml"])
        elif context.scene.global_sdk == 'p3dv3':
            bpy.context.scene.fsx_modeldefpath = ''.join([bpy.context.scene.fsx_sdkpath, "\\Modeling SDK\\bin\\modeldef.xml"])
        elif context.scene.global_sdk == 'p3dv4':
            bpy.context.scene.fsx_modeldefpath = ''.join([bpy.context.scene.fsx_sdkpath, "\\Modeling\\3ds Max\\bin\\modeldef.xml"])
        elif context.scene.global_sdk == 'p3dv5':
            bpy.context.scene.fsx_modeldefpath = ''.join([bpy.context.scene.fsx_sdkpath, "\\Modeling\\3ds Max\\bin\\modeldef.xml"])
        elif context.scene.global_sdk == 'p3dv6':
            bpy.context.scene.fsx_modeldefpath = ''.join([bpy.context.scene.fsx_sdkpath, "\\Modeling\\3ds Max\\bin\\modeldef.xml"])
        else:
            self.report({'INFO'}, "Please select an SDK")
            return {'CANCELLED'}

        bpy.ops.fsx.read_modeldef('INVOKE_DEFAULT')
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Choose Location of SDK")

        if (context.scene.global_sdk == 'fsx'):
            col.label(text="Choose path only up to \Microsoft Flight Simulator X SDK\SDK")
        else:
            col.label(text="Choose path only up to \Lockheed Martin\Prepar3D v.# version")


class FindModelDef(bpy.types.Operator):
    """Set file path to modeldef.xml"""
    bl_label = "Find modeldef.xml"
    bl_idname = "fsx.modeldef_find"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        print(' ModelDef.xml File path = ', self.filepath)  # setup variable to hold filepath
        bpy.context.scene.fsx_modeldefpath = self.filepath
        bpy.ops.fsx.read_modeldef('INVOKE_DEFAULT')
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Choose Location of ModelDef.xml file")
