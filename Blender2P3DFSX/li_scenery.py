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
from . import environment
from . func_scenery import FSXLoadLocation


class FSXLocation(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="name", default="")
    lat: bpy.props.StringProperty(name="lat", default="0.0")
    lon: bpy.props.StringProperty(name="lon", default="0.0")
    alt: bpy.props.FloatProperty(name="alt", default=0.0)
    unit: bpy.props.StringProperty(name="unit", default="M")
    pitch: bpy.props.FloatProperty(name="pitch", default=0.0)
    bank: bpy.props.FloatProperty(name="bank", default=0.0)
    heading: bpy.props.FloatProperty(name="heading", default=0.0)
    no_auto_gen: bpy.props.BoolProperty(name="no_auto_gen", default=False)
    altitude_is_agl: bpy.props.BoolProperty(name="altitude_is_agl", default=False)


class FSXLocationsList(bpy.types.UIList):
    bl_idname = "LOCATIONS_UL_listItem"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name)


bpy.utils.register_class(FSXLocation)
bpy.utils.register_class(FSXLocationsList)
