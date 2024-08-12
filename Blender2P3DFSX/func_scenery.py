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
import sys
import xml.etree.ElementTree as etree
from . import environment


class FSXLoadLocation(bpy.types.Operator):
    bl_label = "Load Location"
    bl_idname = "fsx.remove_location"

    def execute(self, context):
        def decode_bool(value):
            if not value:
                return False
            if value == '1':
                return True
            return False

        # added to catch if the key is not set in the xml file:
        def readBool(location, key):
            value = location.get(key)
            if not value:
                return False
            else:
                return value

        location = context.scene.fsx_locations[context.scene.active_fsx_location]

        if location is None:
            print("Could not find selected location.")
            return {'CANCELLED'}

        context.scene.fsx_Latitude = location.get("lat")
        context.scene.fsx_Longitude = location.get("lon")
        context.scene.fsx_Altitude = location.get("alt")
        context.scene.fsx_altitude_unit = location.get("unit")
        context.scene.fsx_Pitch = location.get("pitch")
        context.scene.fsx_Bank = location.get("bank")
        context.scene.fsx_Heading = location.get("heading")
        context.scene.fsx_bool_noAutogenSup = readBool(location, "no_auto_gen")
        context.scene.fsx_bool_altitude_is_agl = readBool(location, "altitude_is_agl")

        return {'FINISHED'}


class FSXLoadLocation(bpy.types.Operator):
    bl_label = "Load Location"
    bl_idname = "fsx.load_location"

    def execute(self, context):
        def decode_bool(value):
            if not value:
                return False
            if value == '1':
                return True
            return False

        # added to catch if the key is not set in the xml file:
        def readBool(location, key):
            value = location.get(key)
            if not value:
                return False
            else:
                return value

        location = context.scene.fsx_locations[context.scene.active_fsx_location]

        if location is None:
            print("Could not find selected location.")
            return {'CANCELLED'}

        context.scene.fsx_Latitude = location.get("lat")
        context.scene.fsx_Longitude = location.get("lon")
        context.scene.fsx_Altitude = location.get("alt")
        context.scene.fsx_altitude_unit = location.get("unit")
        context.scene.fsx_Pitch = location.get("pitch")
        context.scene.fsx_Bank = location.get("bank")
        context.scene.fsx_Heading = location.get("heading")
        context.scene.fsx_bool_noAutogenSup = readBool(location, "no_auto_gen")
        context.scene.fsx_bool_altitude_is_agl = readBool(location, "altitude_is_agl")

        # hide list:
        context.scene.fsx_bool_loadlocation = False

        return {'FINISHED'}


class FSXAddLocation(bpy.types.Operator):
    """Creates new p3d_locations.xml file or adds location to existing file"""
    bl_label = "Add Location"
    bl_idname = "fsx.add_location"

    def execute(self, context):
        def encode_bool(value):
            if not value:
                return '0'
            if value:
                return '1'
            return '0'

        if bpy.context.scene.fsx_location_name == "":
            print("You need to enter a location name to save the current location settings.")
            return {'CANCELLED'}

        path = os.path.join(bpy.utils.resource_path('USER'), "config\\p3d_locations.xml")
        if os.path.exists(path):
            tree = etree.parse(path)
            root = tree.getroot()
        else:
            root = etree.Element("locations")
            tree = etree.ElementTree(root)

        # find all locations:
        modify = False
        location = root.find(bpy.context.scene.fsx_location_name)
        if location is None:
            location = etree.Element(bpy.context.scene.fsx_location_name)
            root.insert(0, location)
            modify = False
        else:
            modify = True

        location.set("lat", bpy.context.scene.fsx_Latitude)
        location.set("lon", bpy.context.scene.fsx_Longitude)
        location.set("alt", "{}" .format(bpy.context.scene.fsx_Altitude))
        location.set("unit", bpy.context.scene.fsx_altitude_unit)
        location.set("pitch", "{}" .format(bpy.context.scene.fsx_Pitch))
        location.set("bank", "{}" .format(bpy.context.scene.fsx_Bank))
        location.set("heading", "{}" .format(bpy.context.scene.fsx_Heading))
        location.set("no_auto_gen", encode_bool(bpy.context.scene.fsx_bool_noAutogenSup))
        location.set("altitude_is_agl", encode_bool(bpy.context.scene.fsx_bool_altitude_is_agl))

        tree.write(path)

        bpy.ops.fsx.populate_locations('INVOKE_DEFAULT')

        return {'FINISHED'}


# loads all locations from the xml file and populates a the string list. ON
class FSXPopulateLocations(bpy.types.Operator):
    bl_label = "Populate Locations"
    bl_idname = "fsx.populate_locations"

    def execute(self, context):
        def decode_bool(value):
            if not value:
                return False
            if value == '1':
                return True
            return False

        # Ensure all folders of the path exist
        path = os.path.join(bpy.utils.resource_path('USER'), "config\\p3d_locations.xml")
        try:
            tree = etree.parse(path)
        except FileNotFoundError:
            print("Couldn't locate location file at <%s>"%path)
            return {'CANCELLED'}

        root = tree.getroot()

        bpy.context.scene.fsx_locations.clear()
        for location in root:
            item = bpy.context.scene.fsx_locations.add()
            item.name = location.tag
            item.lat = location.get("lat")
            item.lon = location.get("lon")
            item.alt = float(location.get("alt"))
            item.unit = location.get("unit")
            item.pitch = float(location.get("pitch"))
            item.bank = float(location.get("bank"))
            item.heading = float(location.get("heading"))
            item.no_auto_gen = decode_bool(location.get("no_auto_gen"))
            item.altitude_is_agl = decode_bool(location.get("altitude_is_agl"))

        return {'FINISHED'}
