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


class ExportFSXMaterials(Operator, ExportHelper):
    bl_idname = "export_materials.fsx"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export P3D/FSX Materials (*.DDS)"

    filepath: StringProperty(subtype='FILE_PATH')

    # ExportHelper mixin class uses this
    filename_ext = ".dds"

    filter_glob: StringProperty(
        default="*.dds",
        options={'HIDDEN'},
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    ExportSelection: BoolProperty(
        name="Export current selection",
        description="Exports only materials of selected objects on visible layers",
        default=False
    )

    ExportInvertY: BoolProperty(
        name="Invert Y-axis",
        description="Enable to flip all textures vertically",
        default=True
    )

    ExportRedInAlpha: BoolProperty(
        name="Normal Map processing",
        description="Enable to prepare the normal maps for P3D/FSX. This will copy the red channel into the alpha channel and sets the red channel black.",
        default=True
    )

    use_logfile: BoolProperty(
        name="Log File",
        description="Generates a log file in the export folder.",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="You can use this exporter to convert all your textures to .DDS.")
        layout.prop(self, "ExportSelection")
        layout.prop(self, "ExportInvertY")
        layout.prop(self, "ExportRedInAlpha")
        layout.prop(self, "use_logfile")

    def execute(self, context):
        from . func_export_mat import FSXMatExporter
        from . __init__ import bl_info

        MatExporter = FSXMatExporter(self, context, (bl_info.get("version"),))
        MatExporter.Export()
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(os.path.splitext(bpy.data.filepath)[0], ".dds")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
