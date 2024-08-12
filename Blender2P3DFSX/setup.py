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


# This function is crawling through the modeldef.xml file and populates the animation- and attachpoint lists. ON
class ReadModeldef(bpy.types.Operator):
    bl_label = "Reads the Modeldef.xml file and populates the lists"
    bl_idname = "fsx.read_modeldef"

    def execute(self, context):
        if bpy.context.scene.fsx_modeldefpath is None:
            print("Modeldef.xml path not set. Please locate the SDK and the modeldef.xml file.")
            return {'CANCELLED'}
        if bpy.context.scene.fsx_modeldefpath == "":
            print("Modeldef.xml path not set. Please locate the SDK and the modeldef.xml file.")
            return {'CANCELLED'}

        parser = etree.XMLParser(encoding="utf-8")
        try:
            tree = etree.parse(bpy.context.scene.fsx_modeldefpath, parser)
        except FileNotFoundError:
            msg = ("Modeldef file not found under: <%s>"%bpy.context.scene.fsx_modeldefpath)
            raise FileNotFoundError(msg)
        root = tree.getroot()

        pts = ['None', 'ASPHALT', 'BITUMINOUS', 'BRICK', 'CONCRETE', 'CORAL', 'DIRT', 'FOREST',
               'GRASS', 'GRASS_BUMPY', 'GRAVEL', 'HARD_TURF', 'ICE', 'LONG_GRASS', 'MACADAM',
               'OIL_TREATED', 'PLANKS', 'SAND', 'SHALE', 'SHORT_GRASS', 'SNOW', 'STEEL_MATS',
               'TARMAC', 'URBAN', 'WATER', 'WRIGHT_FLYER_TRACK']
        platforms = [(a, a, "") for a in pts]

        bpy.types.Scene.fsx_platform_types = bpy.props.EnumProperty(name="Type", default='None', items=platforms)

        bpy.context.scene.fsx_anims.clear()
        try:
            # this gets rid of p3d stuff from older version of blender2p3d
            bpy.context.scene.p3d_anims.clear()
        except:
            print("p3d_anims found - fixing")

        for anim in root:
            if anim.tag == 'Animation':
                item = bpy.context.scene.fsx_anims.add()
                item.name = anim.attrib['name']
                try:
                    item.length = anim.attrib['length']
                except KeyError:
                    item.length = '0'

        bpy.context.scene.fsx_mouserects.clear()

        try:
            # this gets rid of p3d stuff from older version of blender2p3d
            bpy.context.scene.p3d_mouserects.clear()
        except:
            print("p3d_mouserects found - fixing")

        for vis in root.findall(".PartInfo[Visibility]"):
            item = bpy.context.scene.fsx_visibility.add()
            item.name = vis.find('Name').text

        for mr in root.findall(".PartInfo[MouseRect]"):
            item = bpy.context.scene.fsx_mouserects.add()
            item.name = mr.find('Name').text

        return {'FINISHED'}


class DetectSDK(bpy.types.Operator):
    """Update file path to SDK"""
    bl_label = "Initialize the SDK"
    bl_idname = "fsx.detect_sdk"

    def execute(self, context):
        sdkAutoDetect = context.scene.fsx_bool_autoDetectSDK

        path32 = ""
        path64 = ""
        key = ""
        modeldef_path = ""
        # set the keys and paths, depending on the selected SDK:
        if (context.scene.global_sdk == 'fsx'):
            path32 = r"SOFTWARE\\Microsoft\\Microsoft Games\\Flight Simulator X SDK"
            path64 = r"SOFTWARE\\Wow6432Node\\Microsoft\\Microsoft Games\\Flight Simulator X SDK"
            key = 'SdkRootdir'
            modeldef_path = "Environment Kit\\Modeling SDK\\bin\\modeldef.xml"
        elif (context.scene.global_sdk == 'p3dv1'):
            path32 = r"SOFTWARE\\LockheedMartin\\Prepar3D_SDK"
            path64 = r"SOFTWARE\\Wow6432Node\\LockheedMartin\\Prepar3D_SDK"
            key = 'SetupPath'
            modeldef_path = "\\Environment Kit\\Modeling SDK\\bin\\modeldef.xml"
        elif (context.scene.global_sdk == 'p3dv2'):
            path32 = r"SOFTWARE\\Lockheed Martin\\Prepar3D v2 SDK"
            path64 = r"SOFTWARE\\Wow6432Node\\Lockheed Martin\\Prepar3D v2 SDK"
            key = 'SetupPath'
            modeldef_path = "Modeling SDK\\bin\\modeldef.xml"
        elif (context.scene.global_sdk == 'p3dv3'):
            path32 = r"SOFTWARE\\Lockheed Martin\\Prepar3D v3 SDK"
            path64 = r"SOFTWARE\\Wow6432Node\\Lockheed Martin\\Prepar3D v3 SDK"
            key = 'SetupPath'
            modeldef_path = "Modeling SDK\\bin\\modeldef.xml"
        elif (context.scene.global_sdk == 'p3dv4'):
            path32 = r"SOFTWARE\\Lockheed Martin\\Prepar3D v4 SDK"
            path64 = r"SOFTWARE\\Wow6432Node\\Lockheed Martin\\Prepar3D v4 SDK"
            key = 'SetupPath'
            modeldef_path = "Modeling\\3ds Max\\bin\\modeldef.xml"
        elif (context.scene.global_sdk == 'p3dv5'):
            path32 = r"SOFTWARE\\Lockheed Martin\\Prepar3D v5 SDK"
            path64 = r"SOFTWARE\\Wow6432Node\\Lockheed Martin\\Prepar3D v5 SDK"
            key = 'SetupPath'
            modeldef_path = "Modeling\\3ds Max\\bin\\modeldef.xml"
        elif (context.scene.global_sdk == 'p3dv6'):
            path32 = r"SOFTWARE\\Lockheed Martin\\Prepar3D v6 SDK"
            path64 = r"SOFTWARE\\Wow6432Node\\Lockheed Martin\\Prepar3D v6 SDK"
            key = 'SetupPath'
            modeldef_path = "Modeling\\3ds Max\\bin\\modeldef.xml"
        else:
            print("Please select a valid SDK before initializing the toolset.")
            return {'CANCELLED'}

        # read the SDK at the given location:
        if (sdkAutoDetect is True):
            try:
                # For FSX Windows 64 bit
                handle = OpenKey(HKEY_LOCAL_MACHINE, path64)
                (sdkdir, t) = QueryValueEx(handle, key)
                bpy.context.scene.fsx_sdkpath = sdkdir
                print("sdkpath = ", sdkdir)
                handle.Close()
            except FileNotFoundError:
                # For FSX Windows 32 bit
                handle = OpenKey(HKEY_LOCAL_MACHINE, path32)
                (sdkdir, t) = QueryValueEx(handle, key)
                bpy.context.scene.fsx_sdkpath = sdkdir
                print("sdkpath = ", sdkdir)
                handle.Close()

            bpy.context.scene.fsx_modeldefpath = ''.join([sdkdir, modeldef_path])

            bpy.ops.fsx.read_modeldef('INVOKE_DEFAULT')

            bpy.ops.fsx.populate_locations('INVOKE_DEFAULT')
        else:
            print("Auto SDK False")
            return {'CANCELLED'}

        return {'FINISHED'}
