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

from . environment import *
from . func_util import *
from . li_export import *
from . log_export import Log


class FSXExporter:
    def __init__(self, config, context, version):
        self.config = config
        self.context = context
        self.File = File(self.config.filepath)

        # setting up the log:
        directory = os.path.dirname(self.config.filepath)
        self.logfilepath = Util.ReplaceFileNameExt(self.config.filepath, "-log.txt")
        self.log = Log(context, self.config, self.logfilepath, version)

        try:
            self.modeldefTree = etree.parse(context.scene.fsx_modeldefpath)
        except FileNotFoundError:
            self.log.log("Modeldef.xml file was not found")
            raise FileNotFoundError("Modeldef.xml file not found")

        self.sdkTree = bpy.context.scene.fsx_sdkpath
        self.config.ExportArmatureBones = self.config.ExportSkinWeights  # TODO -put in front end

        # ExportMap maps Blender objects to ExportObjects
        self.log.log("Gathering top-level objects from scene...", False, True)
        ExportMap = {}
        for idx, Object in enumerate(self.context.scene.objects):
            Util.Update_Progress("Progress: ", idx / len(self.context.scene.objects))

            if Object.type == 'EMPTY':
                self.log.log("object found: %s [EMPTY]" % Object.name, True)
                ExportMap[Object] = EmptyExportObject(self.config, self, Object)
            elif Object.type == 'MESH':
                self.log.log("object found: %s [MESH]" % Object.name, True)
                ExportMap[Object] = MeshExportObject(self.config, self, Object)
            elif Object.type == 'ARMATURE':
                self.log.log("object found: %s [ARMATURE]" % Object.name, True)
                ExportMap[Object] = ArmatureExportObject(self.config, self, Object)
                if self.config.ExportSkinWeights and Object.select_get():
                    for Bone in Object.data.bones:
                        ExportMap[Bone] = BoneExportObject(self.config, self, Bone, Object)
        Util.Update_Progress("Progress: ", 1)
        self.log.log("All top-level objects from scene gathered.", False, True)
        self.log.log("")

        # write all children and parents
        self.log.log("Gathering child objects from scene...", False, True)
        for idx, ob in enumerate(ExportMap.values()):
            Util.Update_Progress("Progress: ", idx / len(ExportMap.values()))
            for child in ob.BlenderObject.children:
                ob.Children.append(ExportMap[child])
            if ob.BlenderObject.parent:
                ob.Parent = ExportMap[ob.BlenderObject.parent]
        Util.Update_Progress("Progress: ", 1)
        self.log.log("All child objects from scene gathered.", False, True)
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

        # AnimList contains all animation tags present in the scene
        self.AnimationWriter = None
        self.AnimList = []
        if self.config.ExportAnimation:
            self.log.log("Gathering animation data...", False, True)
            for idx, Object in enumerate(self.ExportList):
                Util.Update_Progress("Progress: ", idx / len(self.ExportList))
                blenObj = Object.BlenderObject
                if blenObj.fsx_anim_tag not in self.AnimList and blenObj.fsx_anim_tag:
                    self.log.log("Animation found for: " + blenObj.name, True)
                    self.AnimList.append(blenObj.fsx_anim_tag)
            Util.Update_Progress("Progress: ", 1)

            # setup generators and writer
            AnimationGenerators = self.__GatherAnimationGenerators()
            self.AnimationWriter = AnimationWriter(self.config,
                                                   self, AnimationGenerators)
            self.log.log("Animation list complete.", False, True)
            self.log.log("")

    def __GatherAnimationGenerators(self):
        Generators = []

        for Object in self.ExportList:
            if Object.type == 'BONE':
                Generators.append(BoneAnimationGenerator(self.config,
                                  None, Object, self.modeldefTree))
            elif (Object.type == 'MESH' or Object.type == 'EMPTY'):
                Generators.append(GenericAnimationGenerator(self.config,
                                  None, Object, self.modeldefTree))

        return Generators

    def Export(self):
        # set current frame to frame 0 before export
        Scene = bpy.context.scene
        BlenderCurrentFrame = Scene.frame_current
        Scene.frame_set(0)

        # open and write data to .x file
        self.File.Open()

        self.log.log("Writing header to X-file", False, True)
        self.__WriteHeader()
        self.log.log("Writing GUID to X-file", False, True)
        self.__WriteGUID()
        self.log.log("Outlining hierarchy in X-file", False, True)
        self.__WriteHierarchy()
        self.log.log()

        # Here is where the fun begins.
        self.log.log("Writing geometry information...", False, True)
        self.__OpenRootFrame()
        for idx, Object in enumerate(self.RootExportList):
            self.log.log("Writing information of %s" % Object.name, True, True)
            Util.Update_Progress("Progress: ", idx / len(self.RootExportList))
            # This one is tricky, due to the changes in Blenders materials:
            Object.Write()
        self.__CloseRootFrame()
        Util.Update_Progress("Progress: ", 1)
        self.log.log("Finished writing geometry information. Closing file.", False, True)
        self.log.log()

        # finishing up...
        self.File.Close()

        # Write gathered animations to .xanim
        if self.AnimationWriter is not None:
            self.AnimationWriter.WriteAnimations(self.modeldefTree)

        # reset current frame
        Scene.frame_set(BlenderCurrentFrame)
        # building .MDL file directly
        if self.config.ExportMDL:
            # XToMDL and ModelDef file paths #####
            if (Scene.global_sdk == 'fsx'):
                XToMdl = ''.join([self.sdkTree, "\\Environment Kit\\Modeling SDK\\3DSM7\\Plugins\\XToMdl.exe"])
                bglComp = ''.join([self.sdkTree, "\\Environment Kit\\BGL Compiler SDK\\BglComp.exe"])
            elif (Scene.global_sdk == 'p3dv1'):
                XToMdl = ''.join([self.sdkTree, "\\Environment Kit\\Modeling SDK\\3DSM7\\Plugins\\XToMdl.exe"])
                bglComp = ''.join([self.sdkTree, "\\Environment Kit\\BGL Compiler SDK\\BglComp.exe"])
            elif (Scene.global_sdk == 'p3dv2'):
                XToMdl = ''.join([self.sdkTree, "\\Modeling SDK\\3DSM7\\Plugins\\XToMdl.exe"])
                bglComp = ''.join([self.sdkTree, "\\Environment SDK\\BGL Compiler SDK\\BglComp.exe"])
            elif (Scene.global_sdk == 'p3dv3'):
                XToMdl = ''.join([self.sdkTree, "\\Modeling SDK\\3DSM7\\Plugins\\XToMdl.exe"])
                bglComp = ''.join([self.sdkTree, "\\Environment SDK\\BGL Compiler SDK\\BglComp.exe"])
            elif (Scene.global_sdk == 'p3dv4'):
                XToMdl = ''.join([self.sdkTree, "\\Modeling\\3ds Max\\Common\\Plugins\\XToMdl.exe"])
                bglComp = ''.join([self.sdkTree, "\\World\\Scenery\\bglcomp.exe"])
            elif (Scene.global_sdk == 'p3dv5'):
                XToMdl = ''.join([self.sdkTree, "\\Modeling\\3ds Max\\Common\\Plugins\\XToMdl.exe"])
                bglComp = ''.join([self.sdkTree, "\\World\\Scenery\\bglcomp.exe"])
            elif (Scene.global_sdk == 'p3dv6'):
                XToMdl = ''.join([self.sdkTree, "\\Modeling\\3ds Max\\Common\\Plugins\\XToMdl.exe"])
                bglComp = ''.join([self.sdkTree, "\\World\\Scenery\\bglcomp.exe"])
            else:
                self.log.log("SDK not specified. Please select a valid SDK version and initialize the SDK paths.", False, True)
                return {'CANCELLED'}

            modeldef = bpy.context.scene.fsx_modeldefpath

            self.log.log()
            self.log.log("======================================================================================================")
            self.log.log("Creating MDL file")
            self.log.log()
            self.log.log("SDK root directory:")
            self.log.log(self.sdkTree)
            self.log.log("XtoMdl.exe path:")
            self.log.log(XToMdl)
            if (self.config.ExportXMLBGL):
                self.log.log("bglcomp.exe path:")
                self.log.log(bglComp)
            self.log.log("======================================================================================================")
            self.log.log()

            self.log.log('''XToMdl.exe (C) Microsoft
    The following output is generated by the tool XToMdl.exe.
    This tool is provided with your P3D/FSX SDK and is in no way
    related to Blender2P3D/FSX author(s), except by its use here.*''')
            self.log.log()
            self.log.log("======================================================================================================")
            self.log.log()
            self.log.log("****************** Begin of XtoMdl.exe output ******************", False, False)
            self.log.log("  -> output currently not logged <-", True, False)  # TODO: add the console output from XtoMdl to the log file.
            # invoke XToMdl.exe
            # all self.config.filepath -> self.FileName
            try:
                additional = ""
                if self.config.use_writeToFile:
                    additional = " /WRITETOFILE"
                if self.config.ExportAnimation:
                    if self.config.ExportXML:
                        spawnv(P_WAIT, XToMdl, ['XToMdl.exe', '/XANIM', additional, '/DICT:"%s"' % modeldef, '/XMLSAMPLE "%s"' % (Util.ReplaceFileNameExt(self.config.filepath, '.x'))])
                    else:
                        spawnv(P_WAIT, XToMdl, ['XToMdl.exe', '/XANIM', additional, '/DICT:"%s"' % modeldef, '"%s"' % (Util.ReplaceFileNameExt(self.config.filepath, '.x'))])
                    assert getsize(Util.ReplaceFileNameExt(self.config.filepath, '.MDL'))
                else:
                    if self.config.ExportXML:
                        spawnv(P_WAIT, XToMdl, ['XToMdl.exe', additional, '/XMLSAMPLE "%s"' % (Util.ReplaceFileNameExt(self.config.filepath, '.x'))])
                    else:
                        spawnv(P_WAIT, XToMdl, ['XToMdl.exe', additional, '"%s"' % (Util.ReplaceFileNameExt(self.config.filepath, '.x'))])
                    assert getsize(Util.ReplaceFileNameExt(self.config.filepath, '.MDL'))
            except:
                if exists(Util.ReplaceFileNameExt(self.config.filepath, '.MDL')):
                    unlink(Util.ReplaceFileNameExt(self.config.filepath, '.MDL'))  # remove 0-length file
                self.log.log("Export to MDL failed. Please check the console for details.", False, True)
                raise ExportError("Export to .MDL failed. XToMdl.exe returned an error.")

            self.log.log("******************** End of XToMdl.exe output ******************", False, False)
            self.log.log()

            try:
                if self.config.ExportXMLBGL:
                    xmlfilefolder = bpy.data.filepath
                    directory = os.path.dirname(xmlfilefolder)
                    self.xmlbglpath = os.path.join(directory, Util.ReplaceFileNameExt(self.config.filepath, ".xml"))
                    self.xmlplacementfile = open(self.xmlbglpath, "w")
                    # create the XML file
                    # Get the GUID of the current object by grabbing it from the file Properties.
                    guid = self.context.scene.fsx_guid

                    lat = self.context.scene.fsx_Latitude
                    lon = self.context.scene.fsx_Longitude
                    alt = "{}{}" .format(self.context.scene.fsx_Altitude, self.context.scene.fsx_altitude_unit)
                    pitch = "{}" .format(self.context.scene.fsx_Pitch)
                    bank = "{}" .format(self.context.scene.fsx_Bank)
                    head = "{}" .format(self.context.scene.fsx_Heading)
                    nosupautogen = self.context.scene.fsx_bool_noAutogenSup
                    if self.context.scene.fsx_bool_altitude_is_agl is False:
                        is_agl = 'FALSE'
                    else:
                        is_agl = 'TRUE'
                    complexity = self.context.scene.fsx_scenery_complexity

                    def valid_guid(guid):
                        regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\Z', re.I)
                        match = regex.match(guid)
                        return bool(match)
                    # check if set
                    if not valid_guid(guid):
                        raise ExportError("Invalid GUID. Verify.")
                    # Define some XML globals that are used often
                    FSXMLVersionLine = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>"
                    FSXMLSchemaLine = "<FSData version=\"9.0\" xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:noNamespaceSchemaLocation=\"bglcomp.xsd\">"
                    # Define the XML format
                    sceneObjLine = "<SceneryObject lat=\"" + lat + "\" lon=\"" + lon + "\" alt=\"" + alt + "\" pitch=\"" + pitch + "\" bank=\"" + bank + "\" heading=\"" + head + "\" altitudeIsAgl=\"" + is_agl + "\" imageComplexity=\"" + complexity + "\">"
                    libObjectLine = "<LibraryObject name=\"{" + guid + "}\" scale=\"1.0\" />"
                    endsceneObjLine = "</SceneryObject>"
                    self.xmlplacementfile.write('%s\n%s\n\n%s\n' % (FSXMLVersionLine, FSXMLSchemaLine, sceneObjLine))
                    # Check to see if other xml options are selected Added By Kris Pyatt
                    if nosupautogen is True:
                        noAGS = "<NoAutogenSuppression />"
                        self.xmlplacementfile.write('%s\n' % (noAGS))
                    # finish building the rest of the xml write libObjectLine, endsceneObjLine
                    self.xmlplacementfile.write('%s\n' % (libObjectLine))
                    self.xmlplacementfile.write('%s\n' % (endsceneObjLine))
                    # If the inlcude MDL in BGL check box is checked then build the MDL file into the BGL file. If the MDL is not present, then warn user and exit.
                    modeldata = "<ModelData sourceFile=\"" + Util.ReplaceFileNameExt(self.config.filepath, '.MDL') + "\" />"
                    self.xmlplacementfile.write('%s\n' % (modeldata))
                    # Finish up the XML and close the file.
                    fsdata = "</FSData>"
                    self.xmlplacementfile.write('%s\n' % (fsdata))
                    self.xmlplacementfile.close()
                    # now the bgl with bglcomp
                    self.log.log("****************** Begin of bglcomp.exe output ******************", False, False)
                    self.log.log("  -> output currently not logged <-", True, False)  # TODO: add the console output from bglComp to the log file.
                    spawnv(P_WAIT, bglComp, ['bglcomp.exe', '"%s"' % (Util.ReplaceFileNameExt(self.config.filepath, '.xml'))])
                    self.log.log("******************** End of bglcomp.exe output ******************", False, False)
                    self.log.log()
                    assert getsize(Util.ReplaceFileNameExt(self.config.filepath, '.BGL'))
            except:
                if exists(Util.ReplaceFileNameExt(self.config.filepath, '.BGL')):
                    unlink(Util.ReplaceFileNameExt(self.config.filepath, '.BGL'))  # remove 0-length file
                self.log.log("BGL compile failed. Please check the console for details.", False, True)
                raise ExportError("Export to .BGL failed. bglcomp.exe returned an error.")

    # Write the .x file header
    def __WriteHeader(self):
        curtime = time.localtime()[0:6]
        (m, n, k) = bpy.app.version

        from . __init__ import bl_info
        version = bl_info.get("version")

        fw = self.File.Write

        # write header + comments
        self.File.Write("xof 0302txt 0032\n\n")
        self.File.Write("// Direct3D .x file translation of context.scene\n")
        self.File.Write("// Generated by Blender %s.%s.%s, Blender2P3D/FSX Version %s\n" % (m, n, k, version))
        self.File.Write("// %.4i-%.2i-%.2i  %.2i:%.2i:%.2i\n\n\n" % (curtime))
        # write X-file templates
        Templates = """template Header {
 <3D82AB43-62DA-11cf-AB39-0020AF71E433>
 WORD major;
 WORD minor;
 DWORD flags;
}

template GuidToName {
 <7419dfe5-b73a-4d66-98d8-c082591dc9e7>
 STRING Guid;
 STRING Name;
}

template Vector {
 <3D82AB5E-62DA-11cf-AB39-0020AF71E433>
 FLOAT x;
 FLOAT y;
 FLOAT z;
}

template ShadowMapReady {
 <2F4F86A9-FE94-4f75-AA1B-299BBD98907B>
 Boolean SMReady;
}

template OverrideBoundingBox {
 <03390521-5EF8-49F0-B6D3-6E91B2068A91>
 Boolean OverrideBoundingBox;
 Vector BoundingBoxMin;
 Vector BoundingBoxMax;
}

template OverrideRadius {
 <6400393B-6210-4917-99C8-968D4DEE0F3A>
 Boolean OverrideRadius;
 FLOAT Radius;
}

template SkinWeight {
 <C3B5EDF9-7345-463d-96D7-6386E2EC4030>
 STRING boneRef;
 FLOAT weight;
}

template SkinWeightGroup {
 <E7B502DB-0C05-4288-A025-80762E19E0AB>
 DWORD nWeights;
 array SkinWeight skinWeights[nWeights];
}

template Coords2d {
 <F6F23F44-7686-11cf-8F52-0040333594A3>
 FLOAT u;
 FLOAT v;
}

template Matrix4x4 {
 <F6F23F45-7686-11cf-8F52-0040333594A3>
 array FLOAT matrix[16];
}

template ColorRGBA {
 <35FF44E0-6C7C-11cf-8F52-0040333594A3>
 FLOAT red;
 FLOAT green;
 FLOAT blue;
 FLOAT alpha;
}

template ColorRGB {
 <D3E16E81-7835-11cf-8F52-0040333594A3>
 FLOAT red;
 FLOAT green;
 FLOAT blue;
}

template TextureFilename {
 <A42790E1-7810-11cf-8F52-0040333594A3>
 STRING filename;
}

template Material {
 <3D82AB4D-62DA-11cf-AB39-0020AF71E433>
 ColorRGBA faceColor;
 FLOAT power;
 ColorRGB specularColor;
 ColorRGB emissiveColor;
 [...]
}

template MeshFace {
 <3D82AB5F-62DA-11cf-AB39-0020AF71E433>
 DWORD nFaceVertexIndices;
 array DWORD faceVertexIndices[nFaceVertexIndices];
}

template MeshTextureCoords {
 <F6F23F40-7686-11cf-8F52-0040333594A3>
 DWORD nTextureCoords;
 array Coords2d textureCoords[nTextureCoords];
}

"""

        self.File.Write(Templates)

        if ((self.context.scene.global_sdk == 'p3dv4') or (self.context.scene.global_sdk == 'p3dv5') or (self.context.scene.global_sdk == 'p3dv6')):
            Templates = """
template MeshTextureCoords2 {
 <564556B9-6802-49AB-8910-31D759C378CF>
 DWORD nTextureCoords;
 array Coords2d textureCoords[nTextureCoords];
}
"""

        self.File.Write(Templates)
        Templates = """
template MeshSkinWeights {
 <C7E2131A-30F3-4eb9-AACC-E0AE11D8FE62>
 DWORD nVertices;
 array SkinWeightGroup skinWeights[nVertices];
}

"""

        self.File.Write(Templates)

#        if self.context.scene.global_SDKset == 'p3d':
        if ((self.context.scene.global_sdk == 'fsx') or (self.context.scene.global_sdk == 'p3dv1')):
            Templates = """
template MeshMaterialList {
 <F6F23F42-7686-11cf-8F52-0040333594A3>
 DWORD nMaterials;
 DWORD nFaceIndexes;
 array DWORD faceIndexes[nFaceIndexes];
 [Material]
}

"""

        else:
            Templates = """
template MeshMaterialList {
 <F6F23F42-7686-11cf-8F52-0040333594A3>
 DWORD nMaterials;
 DWORD nFaceIndexes;
 array DWORD faceIndexes[nFaceIndexes];
 [...]
}

"""

        self.File.Write(Templates)

        Templates = """
template MeshNormals {
 <F6F23F43-7686-11cf-8F52-0040333594A3>
 DWORD nNormals;
 array Vector normals[nNormals];
 DWORD nFaceNormals;
 array MeshFace faceNormals[nFaceNormals];
}

template Mesh {
 <3D82AB44-62DA-11cf-AB39-0020AF71E433>
 DWORD nVertices;
 array Vector vertices[nVertices];
 DWORD nFaces;
 array MeshFace faces[nFaces];
 [...]
}

template BoneInfo {
 <1FF0AE59-4B0B-4dfe-88F2-91D58E395767>
 STRING boneName;
}

template AnimLinkName {
 <0057EC91-F96B-4f5e-9CFB-0E305F39DA1A>
 STRING linkName;
}

template IKChain {
 <2684B333-AAB2-45d9-87D8-6E2BB22616AD>
 STRING chainName;
 STRING startNode;
 STRING endNode;
}

template ConstraintInfo {
 <8713D495-C538-44dc-AE54-1097E7C93D13>
 Boolean bActive;
 Boolean bLimited;
 FLOAT fUpperLimit;
 FLOAT fLowerLimit;
}

// Note that the exported rotation order is YZX
template JointConstraint {
 <BE433CF1-BCC0-43f8-9FE5-DB0556414426>
 array ConstraintInfo Rotation[3];
 array ConstraintInfo Translation[3];
}

template FrameTransformMatrix {
 <F6F23F41-7686-11cf-8F52-0040333594A3>
 Matrix4x4 frameMatrix;
}

template Frame {
 <3D82AB46-62DA-11cf-AB39-0020AF71E433>
 [...]
}
template FloatKeys {
 <10DD46A9-775B-11cf-8F52-0040333594A3>
 DWORD nValues;
 array FLOAT values[nValues];
}

template TimedFloatKeys {
 <F406B180-7B3B-11cf-8F52-0040333594A3>
 DWORD time;
 FloatKeys tfkeys;
}

template AnimationKey {
 <10DD46A8-775B-11cf-8F52-0040333594A3>
 DWORD keyType;
 DWORD nKeys;
 array TimedFloatKeys keys[nKeys];
}

template AnimationOptions {
 <E2BF56C0-840F-11cf-8F52-0040333594A3>
 DWORD openclosed;
 DWORD positionquality;
}

template Animation {
 <3D82AB4F-62DA-11cf-AB39-0020AF71E433>
 [...]
}

template AnimationSet {
 <3D82AB50-62DA-11cf-AB39-0020AF71E433>
 [Animation]
}

template DiffuseTextureFileName {
 <E00200E2-D4AB-481a-9B85-E20F9AE07401>
 STRING filename;
}

template DiffuseTextureUVChannel {
 <E0A8A960-BA3F-4E17-805C-D0B94831BAA4>
 DWORD uvChannel;
}

template SpecularTextureFileName {
 <DF64E0D7-4FFA-4634-9DA0-3EF2FAA081CE>
 STRING filename;
}

template SpecularTextureUVChannel {
 <0E95C17B-0AEF-4D07-BA90-E4B2CD5E01AE>
 DWORD uvChannel;
}

template AmbientTextureFileName {
 <E00200E2-D4AB-481a-9B85-E20F9AE07402>
 STRING filename;
}

template AmbientTextureUVChannel {
 <FAADED67-439E-446F-B96B-5381A0DC731F>
 DWORD uvChannel;
}

template EmissiveTextureFileName {
 <E00200E2-D4AB-481a-9B85-E20F9AE07403>
 STRING filename;
}

template EmissiveTextureUVChannel {
 <F8EF95D3-0307-41C7-9A42-CBE434A97BFA>
 DWORD uvChannel;
}

template ReflectionTextureFileName {
 <E00200E2-D4AB-481a-9B85-E20F9AE07404>
 STRING filename;
}

template ShininessTextureFileName {
 <E00200E2-D4AB-481a-9B85-E20F9AE07405>
 STRING filename;
}

template ShininessTextureUVChannel {
 <98C9B8F8-4A0F-48C7-9886-38299FB8210B>
 DWORD uvChannel;
}

template BumpTextureFileName {
 <E00200E2-D4AB-481a-9B85-E20F9AE07406>
 STRING filename;
}

template BumpTextureUVChannel {
 <12B12581-A164-4D63-AB12-41B2F43F7793>
 DWORD uvChannel;
}

template DisplacementTextureFileName {
 <E00200E2-D4AB-481a-9B85-E20F9AE07407>
 STRING filename;
}

template DisplacementTextureUVChannel {
 <BB58EEEF-9200-42FA-BF5F-4297948CD2BA>
 DWORD uvChannel;
}

template DetailTextureFileName {
 <C223DC28-5C0E-41bc-9706-A30E023EF118>
 STRING filename;
}

template DetailTextureUVChannel {
 <6BCF39C7-4E24-4977-803A-521BABF54D34>
 DWORD uvChannel;
}

template FresnelTextureFileName {
 <C16742E5-974D-4576-870D-2047C79DF7A9>
 STRING filename;
}
"""

        self.File.Write(Templates)

        if ((self.context.scene.global_sdk == 'fsx') or (self.context.scene.global_sdk == 'p3dv1')):
            Templates = """
template FS10Material {
 <16B4B490-C327-42e3-8A71-0FA35C817EA2>
 ColorRGBA FallbackDiffuse;
 ColorRGB  Specular;
 FLOAT     Power;
 FLOAT     DetailScale;
 FLOAT     BumpScale;
 FLOAT     EnvironmentLevelScale;
 Boolean   bUseGlobalEnv;
 Boolean   bModEnvInvDiffuseAlpha;
 Boolean   bModEnvSpecularMapAlpha;
 Boolean   bFresnelDiffuse; Boolean bFresnelSpecular; Boolean bFresnelEnvironment;
 Boolean   bUsePrecipitation;
 Boolean   bPrecipOffset;
 FLOAT     PrecipOffset;
 FLOAT     SpecMapPowerScale;
 STRING    SrcBlend;
 STRING    DstBlend;
 [...]
}
            """

        else:
            Templates = """
template P3DMaterial {
 <16B4B490-C327-42e3-8A71-0FA35C817EA2>
 ColorRGBA FallbackDiffuse;
 ColorRGB  Specular;
 FLOAT     Power;
 FLOAT     DetailScale;
 FLOAT     BumpScale;
 FLOAT     EnvironmentLevelScale;
 Boolean   bUseGlobalEnv;
 Boolean   bModEnvInvDiffuseAlpha;
 Boolean   bModEnvSpecularMapAlpha;
 Boolean   bFresnelDiffuse; Boolean bFresnelSpecular; Boolean bFresnelEnvironment;
 Boolean   bUsePrecipitation;
 Boolean   bPrecipOffset;
 FLOAT     PrecipOffset;
 FLOAT     SpecMapPowerScale;
 STRING    SrcBlend;
 STRING    DstBlend;
 [...]
}
            """

        self.File.Write(Templates)

        Templates = """
template AllowBloom {
 <D66E37C9-9DFE-4092-8565-C6E4C3498235>
 Boolean     AllowBloom;
}

template BloomData {
 <58ED1E67-0D18-44EF-B676-40BB20C1EE88>
 Boolean BloomCopy;
 Boolean BloomModAlpha;
}

template SpecularBloomFloor {
 <21195174-A31D-47ed-BE5A-04ACAD4C3544>
 FLOAT     SpecularBloomFloor;
}

template AmbientLightScale {
 <4CC76AEB-E84F-4688-AB49-E1DC4B9273C7>
 FLOAT     AmbientLightScale;
}

template EmissiveData {
 <A02EF480-3ED3-433d-A71D-5CAC4775757A>
 STRING   EmissiveBlend;
}

template AlphaData {
 <10DB69F3-E0EE-4fb3-8055-63E539EF5885>
 Boolean  ZTestAlpha;
 FLOAT    AlphaTestValue;
 STRING   AlphaTestFunction;
 Boolean  FinalAlphaWrite;
 FLOAT    FinalAlphaWriteValue;
}

template MaskDiffuseBlendsByDetailBlendMask {
 <442265E0-6F93-43C8-8310-C3E1E6848833>
 Boolean  MaskDiffuseBlendsByDetailBlendMask;
}

template MaskFinalAlphaBlendByDetailBlendMask {
 <73671D1D-535E-4DC6-A543-5B226273C5DA>
 Boolean  MaskFinalAlphaBlendByDetailBlendMask;
}

template EnhancedParameters {
 <99CAD20D-DCC5-4ad4-ADAE-ED3CDE30CC02>
 Boolean  AssumeVerticalNormal;
 Boolean  ZWriteAlpha;
 Boolean  NoZWrite;
 Boolean  VolumeShadow;
 Boolean  NoShadow;
 Boolean  PrelitVertices;
}

template BaseMaterialSpecular {
 <E294ED4E-5C5A-4927-B19A-6A2D445FAF24>
 Boolean  AllowBaseMaterialSpecular;
}

template BaseMaterialSkin {
 <B640F860-9E28-4cab-AD46-CACCE2A418AC>
 Boolean  AllowSkinning;
}

template DoubleSidedMaterial {
 <B1C6C3B0-DD1A-417b-919A-B04BAD6AE06D>
 Boolean  DoubleSided;
}

template BlendConstantSetting {
 <48EA96C3-588E-451d-B4BB-0C746C8380D9>
 Boolean  BlendConstant;
}

template ForceTextureAddressWrapSetting {
 <046EE84C-7977-4a11-AA2B-C79FF5391EDD>
 Boolean  ForceTextureAddressWrap;
}

template ForceTextureAddressClampSetting {
 <DB108D57-A3A8-4b76-8CB0-8379CDDEC074>
 Boolean  ForceTextureAddressClamp;
}

template ZBiasValue {
<66F4E05E-94B9-4F07-AE1B-1FFE66810F4E>
FLOAT  ZBias;
}

template NoSpecularBloom {
 <BCE314D2-15DB-4ffd-9F6F-0763B2A4616F>
 Boolean AllowSpecularBloom;
}

template EmissiveBloom {
 <5FF8D7A2-30B5-41bc-A891-28A427D78246>
 Boolean  AllowEmissiveBloom;
}

template BlendDiffuseByBaseAlpha {
 <A623FA7C-37CB-4d17-B702-854E0DBDB467>
 Boolean  BlendDiffByBaseAlpha;
}

template BlendDiffuseByInverseSpecularMapAlpha {
 <DAA68529-1C27-4182-9D97-E631A4759EA7>
 Boolean  BlendDiffuseByInvSpecAlpha;
}

template NNumberTexture {
 <E49E744A-CDBE-40c1-9C89-4A46BEB44D33>
 Boolean  IsNNumberTexture;
}

template MaterialScript {
 <2EE1D70C-4903-4205-AB03-B4A21BF7F323>
 STRING  MaterialScriptFilename;
}

template UseEmissiveAlphaAsHeatMap {
 <F5A3E710-014D-450F-8597-78D00D4AC048>
 Boolean  UseEmissiveAlphaHeatMap;
}

template TemperatureScale {
 <8215033A-0F10-45F0-8493-5C60DC4DD5B5>
 FLOAT  TemperatureScalar;
}

template DetailColor {
 <68E59B99-A9A1-4E27-8660-6B83520657BB>
 ColorRGBA  DetailColor;
}

template DetailTextureParameters {
 <B1D63F06-FCFB-4DCA-B51A-8889A594EBAE>
 FLOAT    DetailOffsetU;
 FLOAT    DetailOffsetV;
 FLOAT    DetailRotation;
 FLOAT    DetailScaleV;
 STRING   DetailBlendMode;
 FLOAT    DetailBlendWeight;
 Boolean  UseDetailAlphaAsBlendMask;
}"""

        self.File.Write(Templates)

        if ((self.context.scene.global_sdk == 'p3dv2') or (self.context.scene.global_sdk == 'p3dv3') or (self.context.scene.global_sdk == 'p3dv4') or (self.context.scene.global_sdk == 'p3dv5') or (self.context.scene.global_sdk == 'p3dv6')):
            Templates = """

template PBRMaterial {
 <91A9F118-F571-4440-B40C-E822088EEBB7>
 ColorRGBA Albedo;
 FLOAT     Metallic;
 FLOAT     Smoothness;
 STRING    RenderMode;
 FLOAT     MaskedThreshold;
 Boolean   AlphaToCoverage;
 Boolean   MetallicHasOcclusion;
 STRING    SmoothnessSource;
 STRING    EmissiveMode;
 Boolean   AssumeVerticalNormal;
 Boolean   Prelit;
 Boolean   DoubleSided;
 DWORD     DecalOrder;
 [...]
}

template AlbedoTextureFileName {
 <23F8BD09-7405-4492-88C9-0428E31DF902>
 STRING filename;
}

template AlbedoTextureUVChannel {
 <61C9E02F-9AB2-4A3E-8849-7FE0A9B56B89>
 DWORD uvChannel;
}

template MetallicTextureFileName {
 <287C8494-CBF8-4050-B2F4-2030D27246FD>
 STRING filename;
}

template MetallicTextureUVChannel {
 <FAF56F68-4C7C-475D-807C-4C1244AF83D7>
 DWORD uvChannel;
}

template NormalTextureFileName {
 <09176F1D-E9F6-4674-8BD2-D89C02CBE19E>
 STRING filename;
}

template NormalTextureUVChannel {
 <C1680BD6-CC82-4390-844A-95B2B80ADE4B>
 DWORD uvChannel;
}

template NormalTextureScale {
 <AAD9D138-F62B-49AF-B09A-DD628D0E2250>
 FLOAT u;
 FLOAT v;
}

template DetailTextureScale {
 <4762DCAD-6B53-4BDA-8464-E85E19B4D8F4>
 FLOAT u;
 FLOAT v;
}
            """
            self.File.Write(Templates)

        if ((self.context.scene.global_sdk == 'p3dv5') or (self.context.scene.global_sdk == 'p3dv6')):
            Templates = """
template MetallicHasReflectance {
<E426288E-6CB9-48A4-9D83-004B3EEA9BE3>
Boolean MetallicHasReflectance;
}
template ClearCoatTextureFileName {
 <5C66613E-CA51-4667-BCB9-42C393205DDC>
 STRING filename;
}

template ClearCoatTextureUVChannel {
 <7FA3BB7D-87D1-4CA7-B8F7-C091AEFE95F1>
 DWORD uvChannel;
}

template ClearCoatContainsNormals {
 <68A8C88B-8FF2-43A0-83DA-17F34D4B3CE1>
 Boolean ContainsNormals;
}
            """
            self.File.Write(Templates)

        Templates = """
template PartData {
 <79B183BA-7E70-44d1-914A-23B304CA91E5>
 DWORD nByteCount;
 array BYTE XMLData[ nByteCount ];
}

Header {
    1;
    0;
    1;
}
        """

        self.File.Write(Templates)

    # write the GUID and friendly name
    def __WriteGUID(self):
        friendly = self.context.scene.fsx_friendly
        guid = self.context.scene.fsx_guid

        def valid_guid(guid):
            regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\Z', re.I)
            match = regex.match(guid)
            return bool(match)
        # check if set
        if friendly == "":
            self.log.log("EXPORT ERROR! Friendly name is not set.")
            raise ExportError("Set friendly name first.")
        if not valid_guid(guid):
            self.log.log("EXPORT ERROR! Invalid GUID.")
            raise ExportError("Invalid GUID. Verify.")
        # check for ASCII characters
        for c in friendly:
            if c >= '\x80':
                self.log.log("EXPORT ERROR! Friendly name must only contain ASCII characters.")
                raise ExportError("Friendly name must be ASCII characters only!")
        friendly = friendly.replace(' ', '_')
        self.File.Write("\nGuidToName {\n    \"{%s}\";\n    \"%s\";\n}\n\n" % (guid, friendly))
        if self.context.scene.fsx_bool_overrideBoundingBox:
            self.File.Write("OverrideBoundingBox {\n1;\n")
            self.File.Write("{:9f};{:9f};{:9f};\n".format(self.context.scene.fsx_bounding_min_x, self.context.scene.fsx_bounding_min_y, self.context.scene.fsx_bounding_min_z))
            self.File.Write("{:9f};{:9f};{:9f};\n".format(self.context.scene.fsx_bounding_max_x, self.context.scene.fsx_bounding_max_y, self.context.scene.fsx_bounding_max_z))
            self.File.Write("}\n\n")
        if self.context.scene.fsx_bool_overrideRadius:
            self.File.Write("OverrideRadius {{\n1;\n{:9f};\n}}\n\n".format(self.context.scene.fsx_radius))
        self.File.Write("ShadowMapReady {\n    0;\n}\n\n\n")

    # write a comment block outlining the scene hierarchy (not necessary)
    def __WriteHierarchy(self):
        self.File.Write("//=====================\n// FILE NODE HIERARCHY\n//=====================\n")
        self.File.Write("// Scene_Root\n")

        # recursive function, writes an object and its children
        def writeobj(obj, level):
            self.File.Write(("// {}" + obj.SafeName + "\n").format("  " * level))
            for Child in Util.SortByNameField(obj.Children):
                writeobj(Child, level + 1)

        for obj in self.RootExportList:
            writeobj(obj, 1)
        self.File.Write("\n")

    # open the root frame with master conversion and scale
    def __OpenRootFrame(self):
        self.File.Write("Frame frm-MasterScale {\n")

        self.File.Write("FrameTransformMatrix {\n\
   0.000977, 0.0, 0.0, 0.0,\n\
   0.0, 0.000977, 0.0, 0.0,\n\
   0.0, 0.0, 0.000977, 0.0,\n\
   0.0, 0.0, 0.0, 1.0;;\n\
}  // End frm-MasterScale FrameTransformMatrix\n")

        self.File.Write("Frame frm-MasterUnitConversion {\n")

        self.File.Write("FrameTransformMatrix {\n\
   1024.000000, 0.0, 0.0, 0.0,\n\
   0.0, 1024.000000, 0.0, 0.0,\n\
   0.0, 0.0, 1024.000000, 0.0,\n\
   0.0, 0.0, 0.0, 1.0;;\n\
}  // End frm-MasterUnitConversion FrameTransformMatrix\n")

        self.File.Write("Frame RotateAroundX {\n")

        # Rotate around X and mirror on z-axis
        self.File.Write("FrameTransformMatrix {\n\
   1.0, 0.0, 0.0, 0.0,\n\
   0.0, 0.0, 1.0, 0.0,\n\
   0.0, 1.0, 0.0, 0.0,\n\
   0.0, 0.0, 0.0, 1.0;;\n\
}  // End Frame RotateAroundX FrameTransformMatrix\n")

        self.File.Indent()

    # close root frame
    def __CloseRootFrame(self):
        self.File.Unindent()
        self.File.Write("} // End of frm-RotateAroundX\n")
        self.File.Write("} // End of frm-MasterUnitConversion\n")
        self.File.Write("} // End of frm-Masterscale\n")


# Writes all animation data to file.
class AnimationWriter:
    def __init__(self, config, Exporter, AnimationGenerators):
        self.config = config
        self.Exporter = Exporter
        self.AnimationGenerators = AnimationGenerators

    # "Public" Interface

    # Writes all AnimationSets.  Implementations probably won't have to override
    # this method.
    def WriteAnimations(self, modeldefTree):
        self.Exporter.log.log("Writing animation data to .xanim...", False, True)

        sourceroot = modeldefTree.getroot()
        root = etree.Element('AnimLib')
        root.set("version", "9.1")
        tree = etree.ElementTree(root)
        # Write each animation of each generator
        for anim in self.Exporter.AnimList:
            element = sourceroot.find(".Animation[@name='%s']" % (anim))
            anim_tag = etree.SubElement(root, "Anim", element.attrib)

            for Generator in self.AnimationGenerators:
                for CurrentAnimation in Generator.Animations:
                    if CurrentAnimation.AnimTag == anim:
                        try:
                            if not anim_tag.attrib['length']:
                                pass
                        except KeyError:
                            anim_tag.set("length", "{:8f}" .format(CurrentAnimation.KeyRange))
                        # write rotation keys
                        self.Exporter.log.log(" * Animation data for %s" % CurrentAnimation.SafeName, False, False)
                        anim_stream = etree.SubElement(anim_tag, "AnimStream")
                        anim_stream.set("name", "Rotation")
                        anim_stream.set("id", "0")
                        anim_stream.set("partName", CurrentAnimation.SafeName)
                        anim_stream.set("length", "{:8f}" .format(CurrentAnimation.KeyRange))
                        for Frame in sorted(CurrentAnimation.RotationKeys.keys()):
                            rot = CurrentAnimation.RotationKeys[Frame]
                            keyframe = etree.SubElement(anim_stream, "Keyframe")
                            keyframe.set("time", "{:8f}" .format(int(Frame)))
                            keyframe.set("data", "{:8f};{:8f};{:8f};{:8f}" .format(-rot[1], -rot[2], -rot[3], rot[0]))
                            keyframe.set("type", "Quaternion")

                        # write position keys
                        anim_stream = etree.SubElement(anim_tag, "AnimStream")
                        anim_stream.set("name", "Location")
                        anim_stream.set("id", "2")
                        anim_stream.set("partName", CurrentAnimation.SafeName)
                        anim_stream.set("length", "{:8f}" .format(CurrentAnimation.KeyRange))
                        for Frame in sorted(CurrentAnimation.PositionKeys.keys()):
                            loc = CurrentAnimation.PositionKeys[Frame]
                            keyframe = etree.SubElement(anim_stream, "Keyframe")
                            keyframe.set("time", "{:8f}" .format(int(Frame)))
                            keyframe.set("data", "{:8f};{:8f};{:8f};0.0" .format(loc[0], loc[1], loc[2]))
                            keyframe.set("type", "Vector")

        # in-place prettyprint formatter
        def indent(elem, level=0):
            i = "\n" + level*"  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    indent(elem, level + 1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i
        # write to file
        indent(root)
        xanimpath = Util.ReplaceFileNameExt(self.config.filepath, ".xanim")
        tree.write(xanimpath, encoding="ISO-8859-1")

        self.Exporter.log.log("Animation file complete.", False, True)
        self.Exporter.log.log()
