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
from datetime import datetime
from bpy.path import basename, ensure_ext


# Interface to the file.  Supports automatic whitespace indenting.
class File:
    def __init__(self, FilePath):
        self.FilePath = FilePath
        self.File = None
        self.__Whitespace = 0

    def Open(self):
        if not self.File:
            self.File = open(self.FilePath, 'w')

    def Close(self):
        self.File.close()
        self.File = None

    def Write(self, String, Indent=True):
        if Indent:
            # Escape any formatting braces
            String = String.replace("{", "{{")
            String = String.replace("}", "}}")
            self.File.write(("{}" + String).format("  " * self.__Whitespace))
        else:
            self.File.write(String)

    def Indent(self, Levels=1):
        self.__Whitespace += Levels

    def Unindent(self, Levels=1):
        self.__Whitespace -= Levels
        if self.__Whitespace < 0:
            self.__Whitespace = 0


# Some general purpose utilities
class Util:
    @staticmethod
    def SafeName(Name):
        # Replaces each character in OldSet with NewChar
        def ReplaceSet(String, OldSet, NewChar):
            for OldChar in OldSet:
                String = String.replace(OldChar, NewChar)
            return String

        import string

        NewName = ReplaceSet(Name, string.punctuation + " ", "_")
        if NewName[0].isdigit() or NewName in ["ARRAY", "DWORD", "UCHAR",
                                               "FLOAT", "ULONGLONG", "BINARY_RESOURCE", "SDWORD", "UNICODE",
                                               "CHAR", "STRING", "WORD", "CSTRING", "SWORD", "DOUBLE", "TEMPLATE"]:
            NewName = "_" + NewName
        return NewName

    @staticmethod
    def WriteMatrix(File, Matrix):
        File.Write("{:9f},{:9f},{:9f},{:9f},\n".format(Matrix[0][0],
                   Matrix[1][0], Matrix[2][0], Matrix[3][0]))
        File.Write("{:9f},{:9f},{:9f},{:9f},\n".format(Matrix[0][1],
                   Matrix[1][1], Matrix[2][1], Matrix[3][1]))
        File.Write("{:9f},{:9f},{:9f},{:9f},\n".format(Matrix[0][2],
                   Matrix[1][2], Matrix[2][2], Matrix[3][2]))
        File.Write("{:9f},{:9f},{:9f},{:9f};;\n".format(Matrix[0][3],
                   Matrix[1][3], Matrix[2][3], Matrix[3][3]))

    # Used on lists of blender objects and lists of ExportObjects, both of
    # which have a name field
    @staticmethod
    def SortByNameField(List):
        def SortKey(x):
            return x.name

        return sorted(List, key=SortKey)

    # Used to set the file name without the extension
    @staticmethod
    def ReplaceFileNameExt(filepath, ext):
        if filepath and ext:
            return ensure_ext(os.path.splitext(filepath)[0], ext)
        else:
            return ""

    @staticmethod
    def LogTime():
        return datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    @staticmethod
    def Update_Progress(job_title, progress):
        # normalize progress to something out of 20
        length = 20  # modify this to change the length
        block = int(round(length * progress))
        msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
        if progress >= 1:
            msg += " DONE " + datetime.now().strftime("%m/%d/%Y %H:%M:%S") + "\r\n"
        sys.stdout.write(msg)
        sys.stdout.flush()
