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
import os
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty


class ExportFSX(Operator, ExportHelper):
    bl_idname = "export_scene.fsx"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export P3D/FSX .X file"

    filepath: StringProperty(subtype='FILE_PATH')

    # ExportHelper mixin class uses this
    filename_ext = ".x"

    filter_glob: StringProperty(
        default="*.x",
        options={'HIDDEN'},
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    ExportSelection: BoolProperty(
        name="Export only current selection",
        description="Export selected objects on visible layers",
        default=False
    )

    ApplyModifiers: BoolProperty(
        name="Apply all modifiers",
        description="Apply modifiers before export",
        default=True
    )

    ExportAnimation: BoolProperty(
        name="Export animations and LOD",
        description="Generates .xanim file with animations",
        default=False
    )

    ExportSkinWeights: BoolProperty(
        name="Skinned mesh",
        description="Export skinned animations",
        default=False
    )

    ExportMDL: BoolProperty(
        name="Export MDL",
        description="Export MDL file",
        default=True
    )

    ExportXMLBGL: BoolProperty(
        name="Export BGL",
        description="Export BGL file and it's XML location file",
        default=False
    )

    ExportXML: BoolProperty(
        name="Export scenery test XML file",
        description="Create and export XML scenery test location file",
        default=False
    )

#       Deactivated. See notes below. ON
#    DebugLog: BoolProperty(
#            name = "Log Verbose",
#            description = "Run in Debug mode, see console for output",
#            default = False
#            )

    use_logfile: BoolProperty(
        name="Log File",
        description="Generates a log file in the export folder.",
        default=True
    )

    # Use Bmp materials (Kris Pyatt)
    use_bmp: BoolProperty(
        name="Use Bmp",
        description="Use Bmp Materials FS9",
        default=False
    )

    use_writeToFile: BoolProperty(
        name="Write to File",
        description="The write to file command is adding an additional step to the export to flush the memory. Use only if you experience OOM errors.",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "ExportSelection")
        row = layout.row()
        row.prop(self, "ApplyModifiers")
        row = layout.row()
        row.prop(self, "ExportAnimation")
        row = layout.row()
        row.prop(self, "ExportSkinWeights")

        row = layout.row()
        row.prop(self, "ExportMDL")
        if ((context.scene.global_sdk == 'p3dv3') or (context.scene.global_sdk == 'p3dv4') or (context.scene.global_sdk == 'p3dv5') or (context.scene.global_sdk == 'p3dv6')):
            row = layout.row()
            row.prop(self, "use_writeToFile")
        row = layout.row()
        row.prop(self, "ExportXMLBGL")
        row = layout.row()
        row.prop(self, "ExportXML")

        # I removed the "DebugLog" and simply log everything in the console.
        # It's not like normal users actually use the console for anything.
        # I left the logfile, but re-wrote how it's handled. There's a dedicated
        # log class defined in log_export.py. I think it's more stream-lined now.
        # ON 2020

        # row = layout.row()
        # row.prop(self, "DebugLog")
        row = layout.row()
        row.prop(self, "use_logfile")
        # Use Bmp materials (Kris Pyatt)
        row = layout.row()
        row.prop(self, "use_bmp")

    def execute(self, context):
        self.filepath = bpy.path.ensure_ext(os.path.splitext(self.filepath)[0], ".x")

        from . func_export import FSXExporter
        from . __init__ import bl_info

        Exporter = FSXExporter(self, context, (bl_info.get("version"),))
        Exporter.Export()
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(os.path.splitext(bpy.data.filepath)[0], ".x")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
