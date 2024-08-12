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
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from . func_util import Util


class ExportError(Exception):
    def __init__(self, msg, objs=None):
        self.msg = msg
        self.objs = objs


# This class wraps a Blender object and writes its data to the file
class ExportObject:  # Base class, do not use
    def __init__(self, config, Exporter, BlenderObject):
        self.config = config
        self.Exporter = Exporter
        self.BlenderObject = BlenderObject

        self.name = self.BlenderObject.name  # Simple alias
        self.type = None
        self.SafeName = Util.SafeName(self.BlenderObject.name)
        self.Children = []
        self.Parent = None
        self.Matrix_local = Matrix()  # 4x4 identity matrix

    def __repr__(self):
        return "[ExportObject: {}]".format(self.BlenderObject.name)


# Simple decorator implemenation for ExportObject.  Used by empty objects
class EmptyExportObject(ExportObject):
    def __init__(self, config, Exporter, BlenderObject):
        ExportObject.__init__(self, config, Exporter, BlenderObject)

        self.type = 'EMPTY'

    def __repr__(self):
        return "[EmptyExportObject: {}]".format(self.name)


class MeshExportObject(ExportObject):
    def __init__(self, config, Exporter, BlenderObject):
        ExportObject.__init__(self, config, Exporter, BlenderObject)

        self.type = 'MESH'

    def __repr__(self):
        return "[MeshExportObject: {}]".format(self.name)
