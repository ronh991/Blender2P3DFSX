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
import time, re, datetime
import xml.etree.ElementTree as etree
import sys
import os
from mathutils import Vector, Matrix, Quaternion
from bpy.path import basename, ensure_ext
from os.path import getsize, exists, splitext
from os import P_WAIT, spawnv, unlink
from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, REG_SZ, REG_EXPAND_SZ
from bpy_types import Bone as bpy_types_Bone, PoseBone as bpy_types_PoseBone
from pathlib import Path

from . environment import *
from . func_util import *
from . li_export_mat import *
from . log_export import Log


class FSXMatExporter:
    def __init__(self, config, context, version):
        self.config = config
        self.context = context
        self.File = File(self.config.filepath)

        # setting up the log:
        filename = Path(bpy.data.filepath).with_suffix('')
        directory = os.path.dirname(self.config.filepath)
        self.logfilepath = Util.ReplaceFileNameExt(filename, "-log.txt")
        self.log = Log(context, self.config, self.logfilepath, version)

        # set up the SDK:
        self.sdkTree = bpy.context.scene.fsx_sdkpath

        # ExportMap maps Blender objects to ExportObjects
        self.log.log("Gathering mesh objects from scene...", False, True)
        ExportMap = {}
        for idx, Object in enumerate(self.context.scene.objects):
            Util.Update_Progress("Progress: ", idx / len(self.context.scene.objects))

            if Object.type == 'MESH':
                self.log.log("object found: %s [MESH]"%Object.name, True)
                ExportMap[Object] = MeshExportObject(self.config, self, Object)
        Util.Update_Progress("Progress: ", 1)
        self.log.log("All mesh objects from scene gathered.", False, True)
        self.log.log("")

        if self.config.ExportSelection:
            self.log.log("Removing un-selected objects from export list", False, True)
            # first, find all roots among exportable types
            RootList = [obj.BlenderObject for obj in ExportMap.values()
                        if obj.BlenderObject.parent is None]
            NoExportList = []

            # recursive function, updates child-parent relation to fit selection
            def swapparent(obj, NoExportList):
                if type(obj) == bpy_types_Bone:
                    BoneObj = ExportMap[obj]
                    Arm = BoneObj.ParentArmature
                    if Arm.select_get():
                        return
                    else:
                        NoExportList.append(obj)
                        for child in obj.children:
                            swapparent(child, NoExportList)
                        return

                if not obj.select_get():
                    NoExportList.append(obj)
                    if ExportMap[obj].Parent:
                        if ExportMap[obj] in ExportMap[obj].Parent.Children:
                            ExportMap[obj].Parent.Children.remove(ExportMap[obj])
                    for child in obj.children:
                        if not ExportMap[obj].Parent:
                            ExportMap[child].Parent = None
                        else:
                            ExportMap[child].Parent = ExportMap[obj].Parent
                            if ExportMap[child] not in ExportMap[obj].Parent.Children:
                                ExportMap[obj].Parent.Children.append(ExportMap[child])
                        swapparent(child, NoExportList)
                else:
                    for child in obj.children:
                        swapparent(child, NoExportList)

            # update children and parents
            for ob in RootList:
                swapparent(ob, NoExportList)

            # remove objects that are not selected
            for ob in NoExportList:
                ExportMap.pop(ob)

            del RootList
            del NoExportList

        # exclude all armatures from export
        ArmList = []
        for ob in ExportMap.values():
            if ob.type == 'ARMATURE':
                arm = ob.BlenderObject
                ArmList.append(arm)
                if ob.Parent:
                    ob.Parent.Children.remove(ob)
                for child in arm.children:
                    if ob.Parent:
                        ExportMap[child].Parent = ExportMap[arm.parent]
                        ExportMap[arm.parent].Children.append(ExportMap[child])
                    else:
                        ExportMap[child].Parent = None
        for arm in ArmList:
            ExportMap.pop(arm)

        # list root level objects to be exported
        self.RootExportList = [Object for Object in ExportMap.values()
                               if Object.Parent is None]

        # tidying up...
        self.RootExportList = Util.SortByNameField(self.RootExportList)
        self.ExportList = Util.SortByNameField(ExportMap.values())
        self.log.log("Export list complete.", False, True)
        self.log.log("")

        print(ExportMap)
        print("Rootlist")
        print(self.RootExportList)

    def Export(self):
        # set current frame to frame 0 before export
        Scene = bpy.context.scene
        BlenderCurrentFrame = Scene.frame_current
        Scene.frame_set(0)
