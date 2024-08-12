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
import sys
from . func_util import Util


class Log():
    # The constructor of the log will now print the disclaimer in the console and the logfile (if selected in the export options)
    def __init__(self, context, config, log_file, toolset_version=""):
        self.config = config
        self.log_file = log_file

        if (self.config.use_logfile is True):
            try:
                f = open(self.log_file, 'w')
                f.close
            except:
                print("WARNING! Could not create log file. Error: %s in %s"%(sys.exc_info()[0], self.log_file))

        # Print the disclaimer:
        print()
        self.log("======================================================================================================")
        self.log("Blender P3D/FSX Toolset version %s " % toolset_version)
        self.log("======================================================================================================")
        self.log()
        self.log('''    Original Toolkit developed by:  Felix Owono-Ateba, 2014
    Updated for Prepar3D by Ron Haertel
    Modifications by Kris Pyatt, 2017
    and Manochvarma Raman, 2018
    Modified for Blender 2.8x by Otmar Nitsche, 2020
    Copyright resides with the authors.''')
        self.log()
        self.log('''    This program comes with NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; see source files for details.''')
        self.log("")
        self.log("======================================================================================================")
        self.log("Using modeldef from:")
        self.log(context.scene.fsx_modeldefpath)
        self.log("Exporting scene to:")
        self.log(self.config.filepath)
        if (self.config.use_logfile is True):
            self.log("Export log file under:")
            self.log(self.log_file)
        self.log("======================================================================================================")
        self.log()

    # Simply use the log(msg) function to print a message. It will always be printed in the console and if the logfile
    # was selected in the options, the message will be written to the log file as well.
    def log(self, msg="", fileonly=False, timestamp=False):
        if (fileonly is False):
            print(msg)
        if (self.config.use_logfile is True):
            with open(self.log_file, 'a') as file:
                if (timestamp is True):
                    msg = "[%s] %s" % (Util.LogTime(), msg)
                # file.write(msg)
                print(msg, file=file)
