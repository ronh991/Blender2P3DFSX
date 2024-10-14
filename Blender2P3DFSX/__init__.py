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
# Further enhancement to the material workflow were coded by:
#   Ron Haertel (2024)
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

bl_info = {
    "name": "P3D/FSX Toolset",
    "author": "Various members of fsdeveloper.com",
    "description": "These tools were developed by members of the fsdeveloper.com community. Felix Owono-Ateba, Ron Haertel, Kris Pyatt (2017), Manochvarma Raman (2018), Otmar Nitsche (2020), David Hoeffgen (2020)",
    "blender": (3, 3, 0),
    "version": (1, 0, 26),
    "location": "View3D",
    "warning": "",
    "category": "3D View",
    "wiki_url": "https://www.fsdeveloper.com/wiki/index.php?title=Blender2P3D/FSX"
}

import bpy

if bpy.app.version < (3, 3, 0):
    raise Exception("This version of the toolset is not compatible with Blender versions less than 3.3.")

from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import auto_load

from . li_visibility import *
from . li_animation import *
from . li_mouserect import *
from . environment import *
from . find_modeldef import *
from . fsx_file import *
from . setup import *

from . func_animation import *
from . func_attachpoint import *
from . func_material import *

from . ui_attachpoint import *
from . ui_animation import *
from . obj_properties import *
from . ui_material import *
from . ui_scenery import *
from . ui_settings import *

from . func_util import *

from . func_export_mat import *
from . ui_export_mat import *

from . func_export import *
from . ui_export import *

auto_load.init()


def register():
    auto_load.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    auto_load.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


def menu_func_export(self, context):
    self.layout.operator(ExportFSX.bl_idname, text="DirectX for P3D/FSX(.x/.mdl)")
