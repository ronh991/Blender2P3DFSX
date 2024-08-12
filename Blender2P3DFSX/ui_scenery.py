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


class PFT_SceneryProperties(bpy.types.Panel):
    bl_idname = "PFT_PT_SceneryProperties"
    bl_label = "Scenery Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "P3D/FSX"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Scenery Properties", icon='LATTICE_DATA')   # add separation for scenenry properties
        layout.label(text="Latitude:")
        layout.prop(context.scene, 'fsx_Latitude')
        layout.label(text="Longitude:")
        layout.prop(context.scene, 'fsx_Longitude')
        row = layout.row().split(factor=0.75)

        row.prop(context.scene, 'fsx_Altitude')
        row.prop(context.scene, 'fsx_altitude_unit')
        layout.prop(context.scene, 'fsx_Pitch')
        layout.prop(context.scene, 'fsx_Bank')
        layout.prop(context.scene, 'fsx_Heading')
        layout.prop(context.scene, 'fsx_bool_altitude_is_agl')
        layout.prop(context.scene, 'fsx_bool_noAutogenSup')

        layout.label(text="Scenery Complexity:")

        layout.prop(context.scene, 'fsx_scenery_complexity')

        box = layout.box()
        box.label(text="Load/Save scenery data", icon='PINNED')
        box.label(text="Location Name:")
        box.prop(context.scene, 'fsx_location_name')
        row = box.row()
        row.operator('fsx.add_location', text="Add", icon='ADD')

        row.prop(context.scene, 'fsx_bool_loadlocation', icon='VIEWZOOM')
        if context.scene.fsx_bool_loadlocation:
            layout.template_list('LOCATIONS_UL_listItem', "", context.scene, 'fsx_locations', context.scene, 'active_fsx_location')
