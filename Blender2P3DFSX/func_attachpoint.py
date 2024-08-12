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


class FSXAttach(bpy.types.Operator):
    """Add selected attach point tag"""
    bl_label = "Attach to object"
    bl_idname = "fsx.attach"

    XMLbody = ""
    XMLroot = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\" ?> <FSMakeMdlData version=\"9.0\"> "
    XMLrootEnd = "</FSMakeMdlData>"
    XMLvis = ""  # Visibility
    XMLnc = ""   # NoCrash
    XMLmr = ""   # MouseRect
    XMLpt = ""   # Platform
    XMLeff = ""  # Effect
    XMLempty = ""

    def SetEmptyAttachPoint(self, context):
        self.XMLempty = ""
        if context.scene.fsx_bool_empty_attach_point and context.scene.fsx_bool_empty_attach_point != 'NONE':
            name = '_'.join(["attachpt", context.scene.fsx_effect_name, "%i" %context.scene.fsx_attachpoint_counter])
            self.XMLempty = "<Attachpoint name=\"{}\"> </Attachpoint> " .format(name)

    def SetVisibility(self, context):
        self.XMLvis = ""
        if context.scene.fsx_bool_vis:
            self.XMLvis = "<Visibility name=\"{}\"> </Visibility> ".format(context.scene.fsx_visibility[context.scene.active_fsx_visibility].name)

    def SetNoCrash(self, context):
        self.XMLnc = ""
        if context.scene.fsx_bool_nocrash and self.obj.type == 'MESH':
            self.XMLnc = "<NoCrash/> "

    def SetMouseRect(self, context):
        self.XMLnr = ""
        if context.scene.fsx_bool_mouserect and self.obj.type == 'MESH':
            self.XMLmr = "<MouseRect name=\"{}\"> </MouseRect> ".format(context.scene.fsx_mouserects[context.scene.active_fsx_mouserect].name)

    def SetPlatform(self, context):
        self.XMLpt = ""
        if context.scene.fsx_bool_platform and self.obj.type == 'MESH' and context.scene.fsx_platform_types != 'None':
            name = '_'.join(["platform", context.scene.fsx_effect_name, "%i" %context.scene.fsx_attachpoint_counter])
            self.XMLpt = "<Platform name=\"{}\" surfaceType=\"{}\" > </Platform> " .format(name, context.scene.fsx_platform_types)

    def SetEffect(self, context):
        self.XMLeff = ""
        if context.scene.fsx_bool_effect:
            name = '_'.join(["attachpt", context.scene.fsx_effect_name, "%i" %context.scene.fsx_attachpoint_counter])
            self.XMLeff = "<Attachpoint name=\"{}\"> <AttachedObject> <Effect effectName=\"{}\" effectParams=\"{}\"/> </AttachedObject> </Attachpoint> " .format(name, context.scene.fsx_effect_file, context.scene.fsx_effect_params)

    def SetFSXxml(self, context, object):
        self.obj = object
        self.SetEmptyAttachPoint(context)
        self.SetVisibility(context)
        self.SetNoCrash(context)
        self.SetMouseRect(context)
        self.SetPlatform(context)
        self.SetEffect(context)
        self.XMLbody = ''.join([self.XMLempty, self.XMLeff, self.XMLvis, self.XMLmr, self.XMLpt, self.XMLnc])
        if self.XMLbody != "":
            self.obj.fsx_xml = ''.join([self.XMLroot, self.XMLbody, self.XMLrootEnd])
            context.scene.fsx_attachpoint_counter += 1
            # TODO: check that Tag 'fsx_xml' contains all selected options

    def execute(self, context):
        self.objlist = context.selected_objects
        count = 0
        for obj in self.objlist:
            self.SetFSXxml(context, obj)
            count += 1
        if self.XMLbody != "":
            self.report({'INFO'}, "Added %i Attachpoint(s)" % count)
        else:
            self.report({'WARNING'}, "Could not add Attachpoint! Check settings.")

        return {'FINISHED'}


class FSXClearAttach(bpy.types.Operator):
    """Remove attach point tag from object"""
    bl_label = "Remove Attach Point"
    bl_idname = "fsx.attach_clear"

    def execute(self, context):
        self.sceneobjects = context.selected_objects
        for ob in self.sceneobjects:
            ob.fsx_xml = ""
        self.report({'INFO'}, "Cleared %i Attachpoint(s)" % len(self.sceneobjects))

        return {'FINISHED'}
