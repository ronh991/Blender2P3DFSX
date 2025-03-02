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

    # "Public" Interface

    def Write(self):
        self._OpenFrame()

        self.Exporter.File.Write("AnimLinkName {{ \"{}\"; }}\n" .format(self.SafeName))
        self._WriteChildren()

        self._CloseFrame()

    # "Protected" Interface
    def _MatrixCompute(self):
        # compute the new matrix_local
        if self.Parent:
            # new @ operator. This is an element-wiseMatrix  multiplication.
            self.Matrix_local = self.Parent.BlenderObject.matrix_world.inverted() @ self.BlenderObject.matrix_world
        else:
            self.Matrix_local = self.BlenderObject.matrix_world

    def _OpenFrame(self):
        self._MatrixCompute()

        self.Exporter.File.Write("Frame frm-{} {{\n".format(self.SafeName))
        self.Exporter.File.Indent()

        # write the attachpoint tag if present
        if self.type != 'BONE':
            if self.BlenderObject.fsx_xml:
                PartData = self.BlenderObject.fsx_xml
                self.Exporter.File.Write("PartData {\n")
                self.Exporter.File.Indent()
                self.Exporter.File.Write("%i;\n" % (len(PartData) + 1))
                for i, char in enumerate(PartData):
                    if i % 10 == 0:
                        self.Exporter.File.Write("%i, " % (ord(char)))
                    else:
                        self.Exporter.File.Write("%i, " % (ord(char)), Indent=False)
                    if i % 10 == 9:
                        self.Exporter.File.Write("\n", Indent=False)
                self.Exporter.File.Write("0;\n", Indent=False)
                self.Exporter.File.Unindent()
                self.Exporter.File.Write("}  // End PartData\n")

        self.Exporter.File.Write("FrameTransformMatrix {\n")
        self.Exporter.File.Indent()
        Util.WriteMatrix(self.Exporter.File, self.Matrix_local)
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")

    def _CloseFrame(self):
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of frm-{}\n".format(self.SafeName))

    def _WriteChildren(self):
        for Child in Util.SortByNameField(self.Children):
            self.Exporter.log.log("Writing information of %s" % Child.name, True, True)
            Child.Write()


# Simple decorator implemenation for ExportObject.  Used by empty objects
class EmptyExportObject(ExportObject):
    def __init__(self, config, Exporter, BlenderObject):
        ExportObject.__init__(self, config, Exporter, BlenderObject)

        self.type = 'EMPTY'

    def __repr__(self):
        return "[EmptyExportObject: {}]".format(self.name)


# Mesh object implementation of ExportObject
class MeshExportObject(ExportObject):
    def __init__(self, config, Exporter, BlenderObject):
        ExportObject.__init__(self, config, Exporter, BlenderObject)

        self.type = 'MESH'

    def __repr__(self):
        return "[MeshExportObject: {}]".format(self.name)

    # "Public" Interface

    def Write(self):  # TODO - optimize! too slow...
        self._OpenFrame()

        self.Exporter.log.log(" * Generating mesh for export...", True, True)
        # Generate the export mesh
        Mesh = None
        ob_eval = None
        if self.config.ApplyModifiers:
            # Certain modifiers shouldn't be applied in some cases
            # Deactivate them until after mesh generation is complete

            DeactivatedModifierList = []

            # If we're exporting armature data, we shouldn't apply
            # armature modifiers to the mesh
            if self.config.ExportSkinWeights:
                DeactivatedModifierList = [Modifier
                                           for Modifier in self.BlenderObject.modifiers
                                           if Modifier.type == 'ARMATURE' and Modifier.show_viewport]

            for Modifier in DeactivatedModifierList:
                Modifier.show_viewport = False

            depsgraph = self.Exporter.context.evaluated_depsgraph_get()
            ob_eval = self.BlenderObject.evaluated_get(depsgraph)
            Mesh = ob_eval.to_mesh()

            # Restore the deactivated modifiers
            for Modifier in DeactivatedModifierList:
                Modifier.show_viewport = True
        else:
            depsgraph = self.Exporter.context.evaluated_depsgraph_get()
            ob_eval = self.BlenderObject.evaluated_get(depsgraph)
            Mesh = ob_eval.to_mesh()

        # process virtual cockpit textures
        # process nNumber texture ??? - missing
        vctextures = []

        for index, mat in enumerate(Mesh.materials):
            if mat is not None:
                #if mat.fsxm_vcpaneltex or mat.fsxm_nnumbertex:
                if mat.fsxm_vcpaneltex:
                    vctextures.append(index)

        if len(vctextures) > 0:
            for poly in Mesh.polygons:
                if poly.material_index in vctextures:
                    for uv_layer in Mesh.uv_layers:
                        for index in poly.loop_indices:
                            v = uv_layer.data[index].uv[1]
                            uv_layer.data[index].uv[1] = 1 - v
        del vctextures

        # triangulate the mesh's faces, or XToMdl will raise warnings
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(Mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(Mesh)
        bm.free()

        self.__WriteMesh(Mesh)

        # Cleanup
        # deprecated.
        # bpy.data.meshes.remove(Mesh)
        # new routine:
        ob_eval.to_mesh_clear()

        self.Exporter.log.log(" * Processing children...", True, True)
        self._WriteChildren()

        self._CloseFrame()

    ###########################################################################
    # "Protected"

    # This class provides a general system for indexing a mesh, depending on
    # exporter needs.  For instance, some options require us to duplicate each
    # vertex of each face, some can reuse vertex data.  For those we'd use
    # _UnrolledFacesMeshEnumerator and _OneToOneMeshEnumerator respectively.
    class _MeshEnumerator:
        def __init__(self, Mesh):
            self.Mesh = Mesh

            # self.vertices and self.PolygonVertexIndexes relate to the
            # original mesh in the following way:

            # Mesh.vertices[Mesh.polygons[x].vertices[y]] ==
            # self.vertices[self.PolygonVertexIndexes[x][y]]

            self.vertices = None
            self.PolygonVertexIndexes = None

    # Represents the mesh as it is inside Blender
    class _OneToOneMeshEnumerator(_MeshEnumerator):
        def __init__(self, Mesh):
            MeshExportObject._MeshEnumerator.__init__(self, Mesh)

            self.vertices = Mesh.vertices

            self.PolygonVertexIndexes = tuple(tuple(Polygon.vertices)
                                              for Polygon in Mesh.polygons)

    # Duplicates each vertex for each face
    class _UnrolledFacesMeshEnumerator(_MeshEnumerator):
        def __init__(self, Mesh):
            MeshExportObject._MeshEnumerator.__init__(self, Mesh)

            self.vertices = tuple()
            for Polygon in Mesh.polygons:
                self.vertices += tuple(Mesh.vertices[VertexIndex]
                                       for VertexIndex in Polygon.vertices)

            self.PolygonVertexIndexes = []
            Index = 0
            for Polygon in Mesh.polygons:
                self.PolygonVertexIndexes.append(tuple(range(Index,
                                                 Index + len(Polygon.vertices))))
                Index += len(Polygon.vertices)

    ###########################################################################
    # "Private" Methods

    def __WriteMesh(self, Mesh):
        self.Exporter.log.log(" * Writing vertices...", True, True)

        self.Exporter.File.Write("Mesh {{ // {} mesh\n".format(self.SafeName))
        self.Exporter.File.Indent()

        # Create the mesh enumerator based on options
        MeshEnumerator = None
        if Mesh.uv_layers or self.config.ExportSkinWeights:
            MeshEnumerator = MeshExportObject._UnrolledFacesMeshEnumerator(Mesh)
        else:
            MeshEnumerator = MeshExportObject._OneToOneMeshEnumerator(Mesh)

        # Write vertex positions
        VertexCount = len(MeshEnumerator.vertices)
        self.Exporter.File.Write("{};\n".format(VertexCount))
        for Index, Vertex in enumerate(MeshEnumerator.vertices):
            Position = Vertex.co
            self.Exporter.File.Write("{:9f};{:9f};{:9f};".format(
                                     Position[0], Position[1], Position[2]))

            if Index == VertexCount - 1:
                self.Exporter.File.Write(";\n", Indent=False)
            else:
                self.Exporter.File.Write(",\n", Indent=False)

        # Write face definitions
        PolygonCount = len(MeshEnumerator.PolygonVertexIndexes)
        self.Exporter.File.Write("{};\n".format(PolygonCount))
        for Index, PolygonVertexIndexes in \
                enumerate(MeshEnumerator.PolygonVertexIndexes):

            self.Exporter.File.Write("{};".format(len(PolygonVertexIndexes)))

            PolygonVertexIndexes = PolygonVertexIndexes[::-1]

            for VertexCountIndex, VertexIndex in \
                    enumerate(PolygonVertexIndexes):

                if VertexCountIndex == len(PolygonVertexIndexes) - 1:
                    self.Exporter.File.Write("{};".format(VertexIndex),
                                             Indent=False)
                else:
                    self.Exporter.File.Write("{},".format(VertexIndex),
                                             Indent=False)

            if Index == PolygonCount - 1:
                self.Exporter.File.Write(";\n", Indent=False)
            else:
                self.Exporter.File.Write(",\n", Indent=False)

        # Write the other mesh components

        self.Exporter.log.log(" * Writing normals...", True, True)
        self.__WriteMeshNormals(Mesh)

        self.Exporter.log.log(" * Writing UV coordinates...", True, True)
        self.__WriteMeshUVCoordinates(Mesh)
        if ((bpy.context.scene.global_sdk == 'p3dv4') or (bpy.context.scene.global_sdk == 'p3dv5') or (bpy.context.scene.global_sdk == 'p3dv6')):
            self.__WriteMeshUVCoordinates2(Mesh)

        self.Exporter.log.log(" * Writing materials...", True, True)
        self.__WriteMeshMaterials(Mesh=Mesh)

        if self.config.ExportSkinWeights:
            self.Exporter.log.log(" * Writing mesh skin weights...", True, True)
            self.__WriteMeshSkinWeights(Mesh=Mesh, MeshEnumerator=MeshEnumerator)

        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} mesh\n".format(self.SafeName))
        self.Exporter.File.Write("AnimLinkName {{ \"{}\"; }}\n" .format(self.SafeName))

    def __WriteMeshNormals(self, Mesh, MeshEnumerator=None):

        # Since mesh normals only need their face counts and vertices per face
        # to match up with the other mesh data, we can optimize export with
        # this enumerator.  Exports each vertex's normal when a face is shaded
        # smooth, and exports the face normal only once when a face is shaded
        # flat.
        class _NormalsMeshEnumerator(MeshExportObject._MeshEnumerator):
            def __init__(self, Mesh):
                MeshExportObject._MeshEnumerator(Mesh)

                self.vertices = []
                self.PolygonVertexIndexes = []

                Index = 0
                for Polygon in Mesh.polygons:
                    if not Polygon.use_smooth:
                        self.vertices.append(Polygon.normal)
                        self.PolygonVertexIndexes.append(
                            tuple(3 * [Index]))
                        Index += 1
                    else:
                        indices = []
                        for VertexIndex in Polygon.vertices:
                            candidate = Mesh.vertices[VertexIndex].normal
                            if candidate in self.vertices:
                                indices.append(self.vertices.index(candidate))
                            else:
                                self.vertices.append(candidate)
                                indices.append(len(self.vertices) - 1)
                                Index += 1
                        self.PolygonVertexIndexes.append(
                            tuple(indices))

        if MeshEnumerator is None:
            MeshEnumerator = _NormalsMeshEnumerator(Mesh)

        self.Exporter.File.Write("MeshNormals {{ // {} normals\n".format(
            self.SafeName))
        self.Exporter.File.Indent()

        # Write mesh normals.
        NormalCount = len(MeshEnumerator.vertices)
        self.Exporter.File.Write("{};\n".format(NormalCount))

        for Index, Vertex in enumerate(MeshEnumerator.vertices):
            Normal = Vertex

            self.Exporter.File.Write("{:9f};{:9f};{:9f};".format(Normal[0],
                                     Normal[1], Normal[2]))

            if Index == NormalCount - 1:
                self.Exporter.File.Write(";\n", Indent=False)
            else:
                self.Exporter.File.Write(",\n", Indent=False)

        # Write face definitions.
        FaceCount = len(MeshEnumerator.PolygonVertexIndexes)
        self.Exporter.File.Write("{};\n".format(FaceCount))

        for Index, Polygon in enumerate(MeshEnumerator.PolygonVertexIndexes):
            # Reverse the winding order
            self.Exporter.File.Write("3;{},{},{};" .format(Polygon[2], Polygon[1], Polygon[0]))

            if Index == FaceCount - 1:
                self.Exporter.File.Write(";\n", Indent=False)
            else:
                self.Exporter.File.Write(",\n", Indent=False)

        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} normals\n".format(
            self.SafeName))

    def __WriteMeshUVCoordinates(self, Mesh):
        if not Mesh.uv_layers or len(Mesh.uv_layers) <= 0:
            return

        self.Exporter.File.Write("MeshTextureCoords {{ // {} UV coordinates\n"
                                 .format(self.SafeName))
        self.Exporter.File.Indent()

        UVCoordinates = Mesh.uv_layers[0].data

        VertexCount = 0
        for Polygon in Mesh.polygons:
            VertexCount += len(Polygon.vertices)

        # Gather and write UV coordinates
        Index = 0
        self.Exporter.File.Write("{};\n".format(VertexCount))
        for Polygon in Mesh.polygons:
            Vertices = []
            for Vertex in [UVCoordinates[Vertex] for Vertex in
                           Polygon.loop_indices]:
                Vertices.append(tuple(Vertex.uv))
            for Vertex in Vertices:
                self.Exporter.File.Write("{:9f};{:9f};".format(Vertex[0],
                                         1.0 - Vertex[1]))
                Index += 1
                if Index == VertexCount:
                    self.Exporter.File.Write(";\n", Indent=False)
                else:
                    self.Exporter.File.Write(",\n", Indent=False)

        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} UV coordinates\n".format(
            self.SafeName))

    # uv coords of the second UV channel
    def __WriteMeshUVCoordinates2(self, Mesh):
        if not Mesh.uv_layers or len(Mesh.uv_layers) <= 1:
            return
        print("__WriteMeshUVCoordinates2 - found")

        self.Exporter.File.Write("MeshTextureCoords2 {{ // {} UV coordinates, channel 2\n"
                                 .format(self.SafeName))
        self.Exporter.File.Indent()

        UVCoordinates = Mesh.uv_layers[1].data
        print("__WriteMeshUVCoordinates2 - data", UVCoordinates)

        VertexCount = 0
        for Polygon in Mesh.polygons:
            VertexCount += len(Polygon.vertices)

        # Gather and write UV coordinates
        Index = 0
        self.Exporter.File.Write("{};\n".format(VertexCount))
        for Polygon in Mesh.polygons:
            Vertices = []
            for Vertex in [UVCoordinates[Vertex] for Vertex in
                           Polygon.loop_indices]:
                Vertices.append(tuple(Vertex.uv))
            for Vertex in Vertices:
                self.Exporter.File.Write("{:9f};{:9f};".format(Vertex[0],
                                         1.0 - Vertex[1]))
                Index += 1
                if Index == VertexCount:
                    self.Exporter.File.Write(";\n", Indent=False)
                else:
                    self.Exporter.File.Write(",\n", Indent=False)

        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} UV 2 coordinates\n".format(
            self.SafeName))

    ###########################################################################
    # Here's the function that caused the looooong wait for the Blender 2.8x update. ON

    def __WriteMeshMaterials(self, Mesh):

        # the following function writes the material to file
        def WriteMaterial(self, Exporter, Material):
            # Function to convert texture names to BMP (Kris Pyatt)
            def useBmp(self):
                materialExt = ".dds"
                if self.Exporter.config.use_bmp is True:
                    materialExt = ".bmp"
                return materialExt

            # This new function will analyse the Material nodes to populate texture file names
            # and values as closely to the Blender Render as possible. ON
            def AnalyzeMaterial(parent, Material):
                # This function is going through all input node of the parameter <node>, until it finds a node of type <node_type>
                # The function will call itself on every non-texture-image nodes to crawl through the whole tree of nodes and links.
                # If <selected_input_node> is passed with a value != -1, ONLY that input slot is being analyzed.
                # Not the most elagant way, but it should work. ON
                def findTextureNode(node, node_type='TEX_IMAGE', selected_input_node=""):
                    check_node = None
                    if node:
                        if selected_input_node != "":
                            if node is not None:
                                node_input = node.inputs[selected_input_node]
                                if ((node_input is not None) and (len(node_input.links) > 0)):
                                    try:
                                        check_node = node_input.links[0].from_node
                                    finally:
                                        if check_node is not None:
                                            if check_node.type == node_type:
                                                return check_node
                                            elif check_node is not None:
                                                check_node = findTextureNode(check_node)
                                                if check_node.type == node_type:
                                                    return check_node
                                            else:
                                                check_node = None
                        else:
                            for idx, node_input in enumerate(node.inputs):
                                if ((node_input is not None) and (len(node_input.links) > 0)):
                                    try:
                                        check_node = node_input.links[0].from_node
                                    finally:
                                        if check_node is not None:
                                            if check_node.type == node_type:
                                                return check_node
                                            elif check_node is not None:
                                                check_node = findTextureNode(check_node)
                                                if check_node.type == node_type:
                                                    return check_node
                                            else:
                                                check_node = None
                    return check_node

                # This function is going through all input node of the parameter <node> and populates the return list
                # with nodes of type <node_type>. ON
                def findTextureNodes(node, node_type='TEX_IMAGE', selected_input_node=""):
                    result = []
                    test_node = None
                    if node:
                        if selected_input_node != "":
                            node_input = node.inputs[selected_input_node]
                            if ((node_input is not None) and (len(node_input.links) > 0)):
                                try:
                                    test_node = node_input.links[0].from_node
                                finally:
                                    if test_node is not None:
                                        if test_node.type == node_type:
                                            result.append(test_node)
                                        elif test_node is not None:
                                            result.extend(findTextureNodes(test_node, node_type))
                        else:
                            for idx, node_input in enumerate(node.inputs):
                                if ((node_input is not None) and (len(node_input.links) > 0)):
                                    try:
                                        test_node = node_input.links[0].from_node
                                    finally:
                                        if test_node is not None:
                                            if test_node.type == node_type:
                                                result.append(test_node)
                                            elif test_node is not None:
                                                result.extend(findTextureNodes(test_node, node_type))

                    return result

                # Use this function to extract the texture file name from a parameter node of type TexImage.
                # It'll does the conversion to BMP if selected in the Exporter UI. ON
                def getTextureFromNode(node, slot_name="", material_name=""):
                    texture = None
                    try:
                        texture = node.image.name
                        bmpMat = useBmp(self)
                        texture = Util.ReplaceFileNameExt(texture, bmpMat)
                    except:
                        self.Exporter.log.log("[%s] no %s texture set." % (material_name, slot_name), True, False)

                    return texture

                # Use this function to return the texture file name from a list of nodes. It returns the filename
                # of the first node that matches it's <name> with <channel_name>.
                # If no texture can be located, the whole node_tree is searched for a node by the name of <channel_name>
                # and the texture of that node is returned.
                def getTextureFromNodes(nodes, channel_name, slot_name, material):
                    texture = ""
                    if len(nodes) == 1:
                        texture = getTextureFromNode(nodes[0], slot_name, material.name)
                    else:
                        for idx, node in enumerate(nodes):
                            if node is not None:
                                if node.name == channel_name:
                                    texture = getTextureFromNode(node, slot_name, material.name)
                    if texture == "":
                        texture = getTextureFromNode(findNodeByLabel(material, channel_name))
                    return texture

                # Use this function to find a node where the <name> matches the <channel_name>. This function is
                # used to look for shader nodes that are currently not hooked up to the BSDF/Specular node. E.g. the
                # Emissive shader node.
                # If no node could be found by name, it runs again to find a node by label. ON
                def findNodeByLabel(Material, channel_name):
                    if Material is not None:
                        for idx, node in enumerate(Material.node_tree.nodes):
                            if node.name == channel_name:
                                return node
                        for idx, node in enumerate(Material.node_tree.nodes):
                            if node.label == channel_name:
                                return node
                    return None

                # An instance of this data block is being filled during the analysis part of the material export.
                # This dictionary is used to hold the texture information for the Material. ON
                data = dict(
                    diffuse_color=[0., 0., 0., 0.],
                    diffuse_texture=None,  # this one is also the albedo map if it's a PBR material
                    specular_color=[0., 0., 0., ],
                    specular_texture=None,  # specular material only
                    emissive_color=[0., 0., 0., 0.],
                    emissive_texture=None,

                    normal_texture=None,
                    normal_scale=0.3,

                    detail_texture=None,
                    fresnel_texture=None,
                    environment_texture=None,
                    # ToDo: need Specular Level (Power)
                    power = 1,
                    metallic_texture=None,  # PBR only
                    # ToDo: have these already just need to set them below
                    metallic_value=0,
                    metallic_smoothness=1,

                    clearcoat_texture=None,
                    clearcoat_value=0,
                    clearcoat_smoothness=1,
                    # missing NNumber
                    #precipitation_texture=None,
                )

                if (Material is not None):
                    print(" Analyse Material", "None" if Material is None else Material.name, "\r\n")
                    # let's catch a problem first. The exporter only works if you use either spec or pbr material.
                    if ((Material.fsxm_material_mode != 'FSX') and (Material.fsxm_material_mode != 'PBR')):
                        msg = format("EXPORT ERROR! The material <%s> is neither FSX nor PBR material!" % Material.name)
                        self.Exporter.log.log(msg, False, True)
                        raise ExportError(msg)

                    # Get the main shader node, based on the selected material type:
                    bsdf_node = None

                    # Might be useful for debugging. Uncomment to print all shader nodes of the material. ON
                    # for this_node in enumerate(Material.node_tree.nodes):
                    #    print("Node %s location(%f,%f)"%(this_node[1].name,this_node[1].location[0],this_node[1].location[1]))

                    if Material.fsxm_material_mode == 'FSX':
                        bsdf_node = Material.node_tree.nodes.get('Specular') or Material.node_tree.nodes.get('Specular BSDF')  # Added or to make exporter work with Blender >= 3.0 Dave_W
                        diffuse_color_node = Material.node_tree.nodes.get('Diffuse Color')
                        specular_color_node = Material.node_tree.nodes.get('Specular Color')
                        power_node = Material.node_tree.nodes.get('Power Factor')
                        #print("FSX")

                    elif Material.fsxm_material_mode == 'PBR':
                        bsdf_node = Material.node_tree.nodes.get('Principled BSDF')
                        base_color_node = Material.node_tree.nodes.get('Base Color')
                        metallic_node = Material.node_tree.nodes.get('Metallic Factor')
                        smoothness_node = Material.node_tree.nodes.get('Smoothness Factor')
                        #print("PBR", bsdf_node ,metallic_node, smoothness_node)

                    if (bsdf_node is None):
                        msg = "ERROR"
                        if (Material.fsxm_material_mode == 'FSX'):
                            msg = format("EXPORT ERROR! Couldn't find the corresponding shader node for material <%s>. It should be a 'Specular BSDF' for specular material." % Material.name)
                        else:
                            msg = format("EXPORT ERROR! Couldn't find the corresponding shader node for material <%s>. It should be a 'Principled BSDF' for PBR material." % Material.name)
                        self.Exporter.log.log(msg, False, True)
                        raise ExportError(msg)
                    else:
                        texture = ""

                        bmpMat = useBmp(self)

                    # 1. diffuse/albedo texture:
                        # ToDo: get this from diffuse color node for SPECULAR and albedo color node for PBR - not bsdf
                        # ToDo: also need to get metallic factor and smoothness (1-roughness)
                        if Material.fsxm_material_mode == 'FSX':
                            
                            n_base_color = diffuse_color_node.outputs.get('Color')
                            n_specular_color = specular_color_node.outputs.get('Color')
                            # get the base color:
                            data["diffuse_color"] = (n_base_color.default_value[0], n_base_color.default_value[1], n_base_color.default_value[2], n_base_color.default_value[3])
                            data["specular_color"] = (n_specular_color.default_value[0], n_specular_color.default_value[1], n_specular_color.default_value[2])
                            # ToDo: set the power - Specular Level
                            data["power"] = power_node.outputs.get('Value').default_value

                        elif Material.fsxm_material_mode == 'PBR':
                            n_base_color = base_color_node.outputs['Color']
                            #print("Base Color", n_base_color)
                            # get the base color:
                            data["diffuse_color"] = (n_base_color.default_value[0], n_base_color.default_value[1], n_base_color.default_value[2], n_base_color.default_value[3])

                        # get the texture:
                        if Material.fsxm_diffusetexture is not None:
                            data["diffuse_texture"] = Util.ReplaceFileNameExt(Material.fsxm_diffusetexture.name, bmpMat)
                        if data["diffuse_texture"] is None:
                            data["diffuse_texture"] = getTextureFromNodes(findTextureNodes(bsdf_node, 'TEX_IMAGE', 'Base Color'), "diffuse", "diffuse/albedo", Material)
                            if data["diffuse_texture"] is not None:
                                print("AnalyzeMaterial - diffuse texture is none - found", data["diffuse_texture"])
                         
                        # check if texture is n number
                        if Material.fsxm_vcpaneltex is True:
                            if data["diffuse_texture"]:
                                data["diffuse_texture"] = Path(data["diffuse_texture"]).stem

                        # check if the texture is a vcockpit gauge
                        #if Material.fsxm_nnumbertex is True:
                        #    if data["diffuse_texture"]:
                        #        data["diffuse_texture"] = Path(data["diffuse_texture"]).stem

                    # 2. Normal map
                        if Material.fsxm_bumptexture is not None:
                            data["normal_texture"] = Util.ReplaceFileNameExt(Material.fsxm_bumptexture.name, bmpMat)
                        data["normal_scale"] = Material.fsxm_normal_scale_x
                        if data["normal_texture"] is None:
                            normal_map_node = Material.node_tree.nodes.get('Normal Map')
                            if normal_map_node is not None:
                                data["normal_texture"] = getTextureFromNodes(findTextureNodes(bsdf_node, 'TEX_IMAGE', 'Normal'), "normal", "normal", Material)
                                if data["normal_texture"] is not None:
                                    print("AnalyzeMaterial - normal texture is none - found", data["normal_texture"])

                    # 3. Reflection map
                        if Material.fsxm_environmentmap is not None:
                            data["environment_texture"] = Util.ReplaceFileNameExt(Material.fsxm_environmentmap.name, bmpMat)

                    # 4. Detail map
                        if Material.fsxm_detailtexture is not None:
                            data["detail_texture"] = Util.ReplaceFileNameExt(Material.fsxm_detailtexture.name, bmpMat)
                        # this will put the diffuse texture into the detailtexture xml - bug
                        # if data["detail_texture"] is None:
                            # data["detail_texture"] = getTextureFromNodes(findTextureNodes(bsdf_node, 'TEX_IMAGE', 'Base Color'), "Detail", "Detail", Material)
                            # if data["detail_texture"] is not None:
                                   # print("AnalyzeMaterial - detail texture is none - found", data["detail_texture"])

                    # 5. Fresnel map
                        if Material.fsxm_fresnelramp is not None:
                            data["fresnel_texture"] = Util.ReplaceFileNameExt(Material.fsxm_fresnelramp.name, bmpMat)

                    # 6. Specular-specific parameters:
                        if Material.fsxm_material_mode == 'FSX':
                        # 6.a Specular texture/color
                            # get the specularity:
                            # ToDo: get this from specular color node
                            #data["specular_color"] = (specular_color_node.inputs.get('Specular').default_value[0], bsdf_node.inputs.get('Specular').default_value[1], bsdf_node.inputs.get('Specular').default_value[2])
                            # get the texture:
                            if Material.fsxm_speculartexture is not None:
                                data["specular_texture"] = Util.ReplaceFileNameExt(Material.fsxm_speculartexture.name, bmpMat)
                            if data["specular_texture"] is None:
                                data["specular_texture"] = getTextureFromNodes(findTextureNodes(bsdf_node, 'TEX_IMAGE', 'Specular'), "specular", "specular", Material)
                                if data["specular_texture"] is not None:
                                    print("AnalyzeMaterial - specular texture is none - found", data["specular_texture"])

                        # 6.b Emissive color
                            # need an emissive color node also
                            n_emissive_color = bsdf_node.inputs.get('Emissive Color')
                            # get the emissive color:
                            data["emissive_color"] = (bsdf_node.inputs.get('Emissive Color').default_value[0], bsdf_node.inputs.get('Emissive Color').default_value[1], bsdf_node.inputs.get('Emissive Color').default_value[2])

                            # get the texture:
                            if Material.fsxm_emissivetexture is not None:
                                data["emissive_texture"] = Util.ReplaceFileNameExt(Material.fsxm_emissivetexture.name, bmpMat)
                            if data["emissive_texture"] is None:
                                data["emissive_texture"] = getTextureFromNodes(findTextureNodes(bsdf_node, 'TEX_IMAGE', 'Emissive Color'), "emissive", "emissive", Material)
                                if data["emissive_texture"] is not None:
                                    print("AnalyzeMaterial - emissive texture is none - found", data["emissive_texture"])

                            # check if the texture is a vcockpit gauge
                            if Material.fsxm_vcpaneltex is True:
                                if data["emissive_texture"]:
                                    data["emissive_texture"] = Path(data["emissive_texture"]).stem

                    # 7. PBR-specific parameters:
                        elif Material.fsxm_material_mode == 'PBR':
                        # 7.a Metallic/smoothness map
                            # ToDo: set the albedo color from node - diffuse above handles that??


                            if Material.fsxm_metallictexture is not None:
                                data["metallic_texture"] = Util.ReplaceFileNameExt(Material.fsxm_metallictexture.name, bmpMat)
                            # if data["metallic_texture"] is None:
                                # data["metallic_texture"] = getTextureFromNodes(findTextureNodes(bsdf_node, 'TEX_IMAGE', 'Metallic'), "metallic", "metallic", Material)
                            # ToDo: set the metallic factor and smoothness (1- roughness) from the nodes not bsdf
                            data["metallic_value"] = metallic_node.outputs[0].default_value
                            data["metallic_smoothness"] = smoothness_node.outputs[0].default_value
                            #print("metallic", metallic_node, smoothness_node)

                        # 7.b Clearcoat/smoothness map
                            if Material.fsxm_clearcoattexture is not None:
                                data["clearcoat_texture"] = Util.ReplaceFileNameExt(Material.fsxm_clearcoattexture.name, bmpMat)
                            if data["clearcoat_texture"] is None:
                                data["clearcoat_texture"] = getTextureFromNodes(findTextureNodes(bsdf_node, 'TEX_IMAGE', 'Clearcoat'), "clearcoat", "clearcoat", Material)
                                data["clearcoat_value"] = bsdf_node.inputs.get('Clearcoat').default_value
                                data["clearcoat_smoothness"] = 1 - bsdf_node.inputs.get('Clearcoat Roughness').default_value
                                if data["clearcoat_texture"] is not None:
                                    print("AnalyzeMaterial - clearcoat texture is none - found", data["clearcoat_texture"])

                        # ToDo: v6 Precipitation map

                return data

            data = AnalyzeMaterial(self, Material)

            if ((Material is not None) and (Material.fsxm_material_mode == 'FSX')):
                Exporter.File.Write("Material {} {{\n".format(Util.SafeName(Material.name)))
                Exporter.File.Indent()
                Exporter.File.Write("{:9f};{:9f};{:9f};{:9f};;\n".format(data["diffuse_color"][0], data["diffuse_color"][1], data["diffuse_color"][2], data["diffuse_color"][3]))
                Exporter.File.Write("{:9f};\n".format(data["power"]))  # specular power ToDo: use a power scale Specular Level scale
                Exporter.File.Write("{:9F};{:9F};{:9F};;\n".format(data["specular_color"][0], data["specular_color"][1], data["specular_color"][2]))
                Exporter.File.Write("{:9f};{:9f};{:9f};;\n".format(data["emissive_color"][0], data["emissive_color"][1], data["emissive_color"][2]))  # Emissive Color
                if ((data["diffuse_texture"] is not None) and (data["diffuse_texture"] != "")):
                    Exporter.File.Write("TextureFilename {{\"{}\";}}\n".format(data["diffuse_texture"]))
                    Exporter.File.Write("DiffuseTextureFilename {{\"{}\";}}\n".format(data["diffuse_texture"]))
                if ((data["emissive_texture"] is not None) and (data["emissive_texture"] != "")):
                    Exporter.File.Write("EmissiveTextureFilename {{\"{}\";}}\n".format(data["emissive_texture"]))
                if ((data["normal_texture"] is not None) and (data["normal_texture"] != "")):
                    Exporter.File.Write("BumpTextureFilename {{\"{}\";}}\n".format(data["normal_texture"]))
                if ((data["environment_texture"] is not None) and (data["environment_texture"] != "")):
                    Exporter.File.Write("ReflectionTextureFilename {{\"{}\";}}\n".format(data["environment_texture"]))
                if ((data["specular_texture"] is not None) and (data["specular_texture"] != "")):
                    Exporter.File.Write("TextureFilename {{\"{}\";}}\n".format(data["specular_texture"]))

                if ((Exporter.context.scene.global_sdk == 'fsx') or (Exporter.context.scene.global_sdk == 'p3dv1')):
                    Exporter.File.Write("FS10Material {\n")
                else:
                    Exporter.File.Write("P3DMaterial {\n")
                Exporter.File.Indent()

                # ToDo: diffuse color and specular color are correct here - will be based on new link structure with Diffuse Color, Specular Color
                # Specular Level, glosiness?, soften?
                Exporter.File.Write("{:9f};{:9f};{:9f};{:9f};;\n".format(data["diffuse_color"][0], data["diffuse_color"][1], data["diffuse_color"][2], data["diffuse_color"][3]))
                Exporter.File.Write("{:9F};{:9F};{:9F};;\n".format(data["specular_color"][0], data["specular_color"][1], data["specular_color"][2]))
                Exporter.File.Write("{:9f};\n".format(data["power"]))  # specular power (specular Level in P3D SDK??? goes to 999)
                Exporter.File.Write("{:9f};{:9f};  // Detail and bump scales\n" .format(Material.fsxm_detailscale, Material.fsxm_bumpscale))
                Exporter.File.Write("{:9f};   // Reflection scale\n" .format(Material.fsxm_refscale))
                Exporter.File.Write("%i;            // Use global env\n" % (Material.fsxm_globenv))
                Exporter.File.Write("%i;            // Blend env by invdifalpha\n" % (Material.fsxm_bledif))
                Exporter.File.Write("%i;            // Blend env by specalpha\n" % (Material.fsxm_blespec))
                Exporter.File.Write("%i; %i; %i;      // Fresnel affects dif - spec - env\n" % (Material.fsxm_fresdif, Material.fsxm_fresspec, Material.fsxm_fresref))
                Exporter.File.Write("%i; %i; " % (Material.fsxm_precipuseprecipitation, Material.fsxm_precipapplyoffset))
                Exporter.File.Write("{:9f};  // Precipitation...\n" .format(Material.fsxm_precipoffs), Indent=False)
                Exporter.File.Write("{:9f};     // Specular Map Power Scale\n" .format(Material.fsxm_specscale))
                Exporter.File.Write("\"{}\"; \"{}\";  // Src/Dest blend\n" .format(Material.fsxm_srcblend, Material.fsxm_destblend))
                Exporter.File.Write("BlendDiffuseByBaseAlpha { %i; }\n" % Material.fsxm_blddif)
                Exporter.File.Write("BlendDiffuseByInverseSpecularMapAlpha { %i; }\n" % Material.fsxm_bldspec)
                Exporter.File.Write("NNumberTexture {\n")
                Exporter.File.Write("    %i;    // Material is an N-Number\n" % (Material.fsxm_nnumbertex))
                Exporter.File.Write("}\n")
                Exporter.File.Write("AllowBloom { %i; }\n" % Material.fsxm_allowbloom)
                Exporter.File.Write("EmissiveBloom {\n")
                Exporter.File.Write("    %i;    // Allow emissive bloom\n" % (Material.fsxm_emissivebloom))
                Exporter.File.Write("}\n")
                Exporter.File.Write("AmbientLightScale {\n")
                Exporter.File.Write("    {:9f};\n" .format(Material.fsxm_ambientlightscale))
                Exporter.File.Write("}\n")
                Exporter.File.Write("BloomData {\n")
                Exporter.File.Write("    %i; %i;    // Bloom material by copying/Bloom material modulating by alpha\n" % (Material.fsxm_bloommaterialcopy, Material.fsxm_bloommaterialmodulatingalpha))
                Exporter.File.Write("}\n")
                Exporter.File.Write("NoSpecularBloom {\n")
                Exporter.File.Write("    %i;    // Allow specular bloom\n" % (Material.fsxm_nospecbloom))
                Exporter.File.Write("}\n")
                Exporter.File.Write("SpecularBloomFloor {\n")
                Exporter.File.Write("    {:9f};\n" .format(Material.fsxm_bloomfloor))
                Exporter.File.Write("}\n")
                Exporter.File.Write("EmissiveData {\n")
                Exporter.File.Write("    \"{}\";\n" .format(Material.fsxm_emissivemode))
                Exporter.File.Write("}\n")
                Exporter.File.Write("AlphaData {\n")
                Exporter.File.Write("    %i;    // ZTest Alpha\n" % (Material.fsxm_ztest))
                Exporter.File.Write("    {:9f}; // Alpha test threshold\n" .format(Material.fsxm_ztestlevel))
                Exporter.File.Write("    \"{}\"; // Alpha test function\n" .format(Material.fsxm_ztestmode))
                Exporter.File.Write("    %i;    // Perform final alpha write\n" % (Material.fsxm_falpha))
                Exporter.File.Write("    {:9f}; // Final alpha value\n" .format(Material.fsxm_falphamult))
                Exporter.File.Write("}\n")
                Exporter.File.Write("EnhancedParameters {\n")
                Exporter.File.Write("    %i;    // Assume vertical normal\n" % (Material.fsxm_assumevertical))
                Exporter.File.Write("    %i;    // Z-Write alpha\n" % (Material.fsxm_zwrite))
                Exporter.File.Write("    %i;    // No Z-Write\n" % (Material.fsxm_nozwrite))
                Exporter.File.Write("    %i;    // Volume shadow\n" % (Material.fsxm_vshadow))
                Exporter.File.Write("    %i;    // No shadow\n" % (Material.fsxm_noshadow))
                Exporter.File.Write("    %i;    // Prelit vertices\n" % (Material.fsxm_pverts))
                Exporter.File.Write("}\n")
                Exporter.File.Write("BaseMaterialSkin {\n")
                Exporter.File.Write("    %i;    // Skinned\n" % (Material.fsxm_skinned))
                Exporter.File.Write("}\n")
                Exporter.File.Write("DoubleSidedMaterial {\n")
                Exporter.File.Write("    %i;    // Double sided\n" % (Material.fsxm_doublesided))
                Exporter.File.Write("}\n")
                Exporter.File.Write("BlendConstantSetting {\n")
                Exporter.File.Write("    %i;    // Blend constant\n" % (Material.fsxm_blendconst))
                Exporter.File.Write("}\n")
                Exporter.File.Write("ForceTextureAddressWrapSetting {\n")
                Exporter.File.Write("    %i;    // Force texture adress wrap\n" % (Material.fsxm_forcewrap))
                Exporter.File.Write("}\n")
                Exporter.File.Write("ForceTextureAddressClampSetting {\n")
                Exporter.File.Write("    %i;    // Force texture adress clamp\n" % (Material.fsxm_forceclamp))
                Exporter.File.Write("}\n")
                if Material.fsxm_nozwrite:
                    Exporter.File.Write("ZBiasValue {\n")
                    Exporter.File.Write("    {:9f}; // ZBiasValue\n" .format(Material.fsxm_zbias))
                    Exporter.File.Write("}\n")
                Exporter.File.Write("BaseMaterialSpecular {\n")
                Exporter.File.Write("    %i;    // Allow Base Material Specular\n" % (not Material.fsxm_nobasespec))
                Exporter.File.Write("}\n")
                Exporter.File.Write("MaskDiffuseBlendsByDetailBlendMask {\n")
                Exporter.File.Write("    %i;    // Mask Diffuse Blends By Detail Blend Mask\n" % (Material.fsxm_MaskDiffuseBlendsByDetailBlendMask))
                Exporter.File.Write("}\n")
                Exporter.File.Write("MaskFinalAlphaBlendByDetailBlendMask {\n")
                Exporter.File.Write("    %i;    // Mask Final Alpha Blend By Detail Blend Mask\n" % (Material.fsxm_MaskFinalAlphaBlendByDetailBlendMask))
                Exporter.File.Write("}\n")
                Exporter.File.Write("UseEmissiveAlphaAsHeatMap {\n")
                Exporter.File.Write("    %i;    // Use Emissive Map as Alpha Heat Map\n" % (Material.fsxm_UseEmissiveAlphaAsHeatMap))
                Exporter.File.Write("}\n")
                Exporter.File.Write("DiffuseTextureUVChannel {\n")
                Exporter.File.Write("   %i;\n" % (Material.fsxm_DiffuseTextureUVChannel))
                Exporter.File.Write("}\n")
                Exporter.File.Write("SpecularTextureUVChannel {\n")
                Exporter.File.Write("   %i;\n" % (Material.fsxm_SpecularTextureUVChannel))
                Exporter.File.Write("}\n")
                Exporter.File.Write("BumpTextureUVChannel {\n")
                Exporter.File.Write("   %i;\n" % (Material.fsxm_BumpTextureUVChannel))
                Exporter.File.Write("}\n")
                Exporter.File.Write("DetailTextureUVChannel {\n")
                Exporter.File.Write("   %i;\n" % (Material.fsxm_DetailTextureUVChannel))
                Exporter.File.Write("}\n")
                Exporter.File.Write("EmissiveTextureUVChannel {\n")
                Exporter.File.Write("   %i;\n" % (Material.fsxm_EmissiveTextureUVChannel))
                Exporter.File.Write("}\n")

                print("export fsxm_script", Exporter.context.scene.global_sdk )
                if (((Exporter.context.scene.global_sdk == 'fsx') or (Exporter.context.scene.global_sdk == 'p3dv5') or (Exporter.context.scene.global_sdk == 'p3dv6')) and Material.fsxm_MaterialScript != ""):
                    print("fsxm_script - has script file", Material.fsxm_MaterialScript, Path(Material.fsxm_MaterialScript).name)
                    Exporter.File.Write("MaterialScript {\n")
                    fsxm_MaterialScript_filename = Path(Material.fsxm_MaterialScript).name
                    Exporter.File.Write("    \"{}\"; // MaterialScript\n" .format(fsxm_MaterialScript_filename))
                    Exporter.File.Write("}\n")

                Exporter.File.Write("TemperatureScale {\n")
                Exporter.File.Write("    {:9f}; // Temperature Scale\n" .format(Material.fsxm_TemperatureScale))
                Exporter.File.Write("}\n")
                Exporter.File.Write("DetailColor {\n")
                Exporter.File.Write("{:9f};{:9f};{:9f};{:9f};\n".format(Material.fsxm_DetailColor[0],
                                    Material.fsxm_DetailColor[1], Material.fsxm_DetailColor[2], Material.fsxm_DetailColor[3]))
                Exporter.File.Write("}\n")
                Exporter.File.Write("DetailTextureParameters {\n")
                Exporter.File.Write("    {:9f}; // Detail Offset U\n" .format(Material.fsxm_DetailOffsetU))
                Exporter.File.Write("    {:9f}; // Detail Offset V\n" .format(Material.fsxm_DetailOffsetV))
                Exporter.File.Write("    {:9f}; // Detail Rotation\n" .format(Material.fsxm_DetailRotation))
                Exporter.File.Write("    {:9f}; // Detail Scale V\n" .format(Material.fsxm_DetailScaleV)) # strange that 3DS calls this DetailScaleU
                Exporter.File.Write("    \"{}\"; // Detail Blend Mode\n" .format(Material.fsxm_DetailBlendMode))
                Exporter.File.Write("    {:9f}; // Detail Blend Weight\n" .format(Material.fsxm_DetailBlendWeight))
                Exporter.File.Write("    %i; // Use Detail Alpha As Blend Mask\n" % (Material.fsxm_UseDetailAlphaAsBlendMask))
                Exporter.File.Write("}\n")

                if ((data["diffuse_texture"] is not None) and (data["diffuse_texture"] != "")):
                    Exporter.File.Write("DiffuseTextureFilename {{\"{}\";}}\n".format(data["diffuse_texture"]))
                if ((data["specular_texture"] is not None) and (data["specular_texture"] != "")):
                    Exporter.File.Write("SpecularTextureFilename {{\"{}\";}}\n".format(data["specular_texture"]))
                if ((data["emissive_texture"] is not None) and (data["emissive_texture"] != "")):
                    Exporter.File.Write("EmissiveTextureFilename {{\"{}\";}}\n".format(data["emissive_texture"]))
                if ((data["normal_texture"] is not None) and (data["normal_texture"] != "")):
                    Exporter.File.Write("BumpTextureFilename {{\"{}\";}}\n".format(data["normal_texture"]))

                if ((data["environment_texture"] is not None) and (data["environment_texture"] != "")):
                    Exporter.File.Write("ReflectionTextureFileName {{\"{}\";}}\n".format(data["environment_texture"]))
                if ((data["fresnel_texture"] is not None) and (data["fresnel_texture"] != "")):
                    Exporter.File.Write("FresnelTextureFileName {{\"{}\";}}\n".format(data["fresnel_texture"]))
                if ((data["detail_texture"] is not None) and (data["detail_texture"] != "")):
                    Exporter.File.Write("DetailTextureFileName {{\"{}\";}}\n".format(data["detail_texture"]))

                Exporter.File.Unindent()
                if ((Exporter.context.scene.global_sdk == 'fsx') or (Exporter.context.scene.global_sdk == 'p3dv1')):
                    Exporter.File.Write("} // End of FS10Material\n")
                else:
                    Exporter.File.Write("} // End of P3DMaterial\n")

                Exporter.File.Unindent()
                Exporter.File.Write("} // End of Material\n")

            elif ((Material is not None) and (Material.fsxm_material_mode == 'PBR')):
                Exporter.File.Write("PBRMaterial {} {{\n".format(Util.SafeName(Material.name)))
                Exporter.File.Indent()
                Exporter.File.Write("{:9f};{:9f};{:9f};{:9f};;\n".format(data["diffuse_color"][0], data["diffuse_color"][1], data["diffuse_color"][2], data["diffuse_color"][3]))
                Exporter.File.Write("{:9F};\n".format(data["metallic_value"]))
                Exporter.File.Write("{:9F};\n".format(data["metallic_smoothness"]))
                Exporter.File.Write("\"%s\";\n" % Material.fsxm_rendermode)  # Render mode
                Exporter.File.Write("{:9F};\n".format(Material.fsxm_maskedthreshold))  # Masked Threshold
                if Material.fsxm_alphatocoverage is False:
                    Exporter.File.Write("0;\n")  # Alpha to Coverage
                else:
                    Exporter.File.Write("1;\n")  # Alpha to Coverage
                if Material.fsxm_metallichasocclusion is False:
                    Exporter.File.Write("0;\n")  # Has metallic occlusion map
                else:
                    Exporter.File.Write("1;\n")  # Has metallic occlusion map
                Exporter.File.Write("\"%s\";\n" % Material.fsxm_metallicsource)
                Exporter.File.Write("\"%s\";\n" % Material.fsxm_emissivemode_pbr)
                Exporter.File.Write("%i;\n" % (Material.fsxm_assumevertical))
                Exporter.File.Write("%i;\n" % (Material.fsxm_pverts))
                Exporter.File.Write("%i;\n" % (Material.fsxm_doublesided))
                Exporter.File.Write("%i;\n" % (Material.fsxm_decalorder))

                if ((data["diffuse_texture"] is not None) and (data["diffuse_texture"] != "")):
                    Exporter.File.Write("AlbedoTextureFileName {{\"{}\";}}\n".format(data["diffuse_texture"]))
                if ((data["metallic_texture"] is not None) and (data["metallic_texture"] != "")):
                    Exporter.File.Write("MetallicTextureFileName {{\"{}\";}}\n".format(data["metallic_texture"]))
                if ((data["normal_texture"] is not None) and (data["normal_texture"] != "")):
                    Exporter.File.Write("NormalTextureFileName {{\"{}\";}}\n".format(data["normal_texture"]))
                if ((data["emissive_texture"] is not None) and (data["emissive_texture"] != "")):
                    Exporter.File.Write("EmissiveTextureFileName {{\"{}\";}}\n".format(data["emissive_texture"]))
                if ((data["detail_texture"] is not None) and (data["detail_texture"] != "")):
                    Exporter.File.Write("DetailTextureFileName {{\"{}\";}}\n".format(data["detail_texture"]))
                if ((data["clearcoat_texture"] is not None) and (data["clearcoat_texture"] != "")):
                    Exporter.File.Write("ClearcoatTextureFileName {{\"{}\";}}\n".format(data["clearcoat_texture"]))

                Exporter.File.Write("AlbedoTextureUVChannel { %i; }\n" % Material.fsxm_AlbedoTextureUVChannel)
                Exporter.File.Write("MetallicTextureUVChannel { %i; }\n" % Material.fsxm_MetallicTextureUVChannel)
                Exporter.File.Write("NormalTextureUVChannel { %i; }\n" % Material.fsxm_BumpTextureUVChannel)
                Exporter.File.Write("EmissiveTextureUVChannel { %i; }\n" % Material.fsxm_EmissiveTextureUVChannel)
                Exporter.File.Write("DetailTextureUVChannel { %i; }\n" % Material.fsxm_DetailTextureUVChannel)
                Exporter.File.Write("ClearcoatTextureUVChannel { %i; }\n" % Material.fsxm_ClearcoatTextureUVChannel)

                if ((Material.fsxm_metallichasreflection) and (Exporter.context.scene.global_sdk == 'p3dv5') or (Material.fsxm_metallichasreflection) and (Exporter.context.scene.global_sdk == 'p3dv6')):
                    Exporter.File.Write("MetallicHasReflectance { 1; }\n")

                if ((Material.fsxm_clearcoatcontainsnormals) and (Exporter.context.scene.global_sdk == 'p3dv5') or (Material.fsxm_clearcoatcontainsnormals) and (Exporter.context.scene.global_sdk == 'p3dv6')):
                    Exporter.File.Write("ClearCoatContainsNormals { 1; }\n")  # Changed to ClearCoatContainsNormals for compatibility with MCX Dave_W

                Exporter.File.Write("NormalTextureScale {\n")
                Exporter.File.Indent()
                Exporter.File.Write("{:9F};\n".format(Material.fsxm_normal_scale_x))
                Exporter.File.Write("{:9F};\n".format(Material.fsxm_normal_scale_y))
                Exporter.File.Unindent()
                Exporter.File.Write("}\n")
                Exporter.File.Write("DetailTextureScale {\n")
                Exporter.File.Indent()
                Exporter.File.Write("{:9F};\n".format(Material.fsxm_detail_scale_x))
                Exporter.File.Write("{:9F};\n".format(Material.fsxm_detail_scale_y))
                Exporter.File.Unindent()
                Exporter.File.Write("}\n")

                if Material.fsxm_MaterialScript != "":
                    Exporter.File.Write("MaterialScript {\n")
                    fsxm_MaterialScript_filename = Path(Material.fsxm_MaterialScript).name
                    Exporter.File.Write("    \"{}\"; // MaterialScript\n" .format(fsxm_MaterialScript_filename))
                    #Exporter.File.Write("    \"{}\"; // MaterialScript\n" .format(Material.fsxm_MaterialScript))
                    Exporter.File.Write("}\n")

                Exporter.File.Unindent()
                Exporter.File.Write("} // End of PBRMaterial\n")

        # gather object's materials
        Materials = Mesh.materials
        # Do not write materials if there are none
        if not Materials.keys():
            return

        print(" Mesh", Mesh.name)
        self.Exporter.File.Write("MeshMaterialList {{ // {} material list\n".
                                 format(self.SafeName))
        self.Exporter.File.Indent()

        self.Exporter.File.Write("{};\n".format(len(Materials)))
        self.Exporter.File.Write("{};\n".format(len(Mesh.polygons)))

        # Write a material index for each face
        for Index, Polygon in enumerate(Mesh.polygons):
            self.Exporter.File.Write("{}".format(Polygon.material_index))
            if Index == len(Mesh.polygons) - 1:
                self.Exporter.File.Write(";\n", Indent=False)
            else:
                self.Exporter.File.Write(",\n", Indent=False)

        for Material in Materials:
            WriteMaterial(self, self.Exporter, Material)

        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} material list\n".format(self.SafeName))

    def __WriteMeshSkinWeights(self, Mesh, MeshEnumerator=None):
        # This contains vertex indexes and weights for the vertices that belong
        # to this bone's group.  Also calculates the bone skin matrix.
        class _BoneVertexGroup:
            def __init__(self, BlenderObject, ArmatureObject, BoneName):
                self.BoneName = BoneName
                self.SafeName = Util.SafeName(ArmatureObject.name) + "_" + \
                    Util.SafeName(BoneName)

                self.Indexes = []
                self.Weights = []

                # BoneMatrix transforms mesh vertices into the
                # space of the bone.
                # Here are the final transformations in order:
                #  - Object Space to World Space
                #  - World Space to Armature Space
                #  - Armature Space to Bone Space
                # This way, when BoneMatrix is transformed by the bone's
                # Frame matrix, the vertices will be in their final world
                # position.

                self.BoneMatrix = ArmatureObject.data.bones[BoneName] \
                    .matrix_local.inverted()
                self.BoneMatrix = self.BoneMatrix @ ArmatureObject.matrix_world.inverted()
                self.BoneMatrix = self.BoneMatrix @ BlenderObject.matrix_world

                def AddVertex(self, Index, Weight):
                    self.Indexes.append(Index)
                    self.Weights.append(Weight)

        # Skin weights work well with vertex reuse per face.  Use a
        # _OneToOneMeshEnumerator if possible.
        if MeshEnumerator is None:
            MeshEnumerator = MeshExportObject._UnrolledFacesMeshEnumerator(Mesh)

        ArmatureModifierList = [Modifier
                                for Modifier in self.BlenderObject.modifiers
                                if Modifier.type == 'ARMATURE' and Modifier.show_viewport]

        if not ArmatureModifierList:
            return

        # Although multiple armature objects are gathered, support for
        # multiple armatures per mesh is not complete
        ArmatureObjects = [Modifier.object for Modifier in ArmatureModifierList]

        for ArmatureObject in ArmatureObjects:
            if ArmatureObject is not None:
                # Determine the names of the bone vertex groups
                PoseBoneNames = [Bone.name for Bone in ArmatureObject.pose.bones]
                VertexGroupNames = [Group.name for Group
                                    in self.BlenderObject.vertex_groups]
                UsedBoneNames = set(PoseBoneNames).intersection(VertexGroupNames)

                # Create a _BoneVertexGroup for each group name
                BoneVertexGroups = [_BoneVertexGroup(self.BlenderObject,
                                    ArmatureObject, BoneName) for BoneName in UsedBoneNames]

                # Maps Blender's internal group indexing to our _BoneVertexGroups
                GroupIndexToBoneVertexGroups = {Group.index: BoneVertexGroup
                                                for Group in self.BlenderObject.vertex_groups
                                                for BoneVertexGroup in BoneVertexGroups
                                                if Group.name == BoneVertexGroup.BoneName}

                MaximumInfluences = 4

                self.Exporter.File.Write("MeshSkinWeights {\n")
                self.Exporter.File.Write("%i;\n" % len(MeshEnumerator.vertices))
                self.Exporter.File.Indent()

                for Index, Vertex in enumerate(MeshEnumerator.vertices):
                    VertexWeightTotal = 0.0
                    VertexInfluences = 0
                    relVertexGroups = []

                    # Sum up the weights of groups that correspond
                    # to armature bones.
                    for VertexGroup in Vertex.groups:
                        BoneVertexGroup = GroupIndexToBoneVertexGroups.get(VertexGroup.group)
                        if BoneVertexGroup is not None:
                            relVertexGroups.append(VertexGroup)
                            VertexWeightTotal += VertexGroup.weight
                            VertexInfluences += 1

                    # bubble sort to go through the vertex group:
                    def groupSort(myVertexGroup):
                        if myVertexGroup is None:
                            return

                        n = len(myVertexGroup)

                        # Traverse through all array elements
                        for i in range(n):

                            # Last i elements are already in place
                            for j in range(0, n - i - 1):

                                # traverse the array from 0 to n-i-1
                                # Swap if the element found is greater
                                # than the next element
                                if myVertexGroup[j].weight <= myVertexGroup[j + 1].weight:
                                    myVertexGroup[j], myVertexGroup[j + 1] = myVertexGroup[j + 1], myVertexGroup[j]

                    # Let's make the weights a bit smarter. ON.
                    if (VertexInfluences > MaximumInfluences) and (len(relVertexGroups) > 0):
                        groupSort(relVertexGroups)
                        relVertexGroups = relVertexGroups[:MaximumInfluences]

                    # Write the weights to file
                    # normalizing each bone's weight.
                    self.Exporter.File.Write("{};\n".format(len(relVertexGroups)))  # VertexInfluences))
                    self.Exporter.File.Indent()

                    for VertexGroup in relVertexGroups:
                        BoneVertexGroup = GroupIndexToBoneVertexGroups.get(VertexGroup.group)
                        if BoneVertexGroup is not None:
                            self.Exporter.File.Write("\"{}\",".format(BoneVertexGroup.SafeName))
                            if VertexWeightTotal > 0.0:     # added to catch divide by zero error. ON.
                                self.Exporter.File.Write("{:9f};\n".format(VertexGroup.weight / VertexWeightTotal), Indent=False)
                            else:
                                self.Exporter.File.Write("{:9f};\n".format(0.0), Indent=False)
                    if Vertex.groups is None:
                        BoneVertexGroup = GroupIndexToBoneVertexGroups.get(0)
                        self.Exporter.File.Write("\"{}\",".format(BoneVertexGroup.SafeName))
                        self.Exporter.File.Write("{:9f};\n".format(0.0), Indent=False)
                    self.Exporter.File.Unindent()

                self.Exporter.File.Unindent()
                self.Exporter.File.Write("} // End MeshSkinWeights\n")


# Armature object implementation of ExportObject
class ArmatureExportObject(ExportObject):
    def __init__(self, config, Exporter, BlenderObject):
        ExportObject.__init__(self, config, Exporter, BlenderObject)

        self.type = 'ARMATURE'

    def __repr__(self):
        return "[ArmatureExportObject: {}]".format(self.name)

    # "Public" Interface

    def Write(self):
        self.Exporter.log.log("Opening frame for {}".format(self), True, True)
        self._OpenFrame()

        Armature = self.BlenderObject.data
        RootBones = [Bone for Bone in Armature.bones if Bone.parent is None]
        print("Armature pose position", Armature.pose_position)
        self.config.ExportBonePosition = Armature.pose_position
        self.Exporter.log.log("Writing frames for armature bones...", False, True)
        self.__WriteBones(RootBones)
        self.Exporter.log.log("Done", False, True)

        self.Exporter.log.log("Writing children of {}".format(self), True, True)
        self._WriteChildren()

        self._CloseFrame()
        self.Exporter.log.log("Closed frame of {}".format(self), True, True)

        # IKChain for IKChain IK_MainHandle, IK_SecondaryHandle, IK_WheelsGroundLock needs to be done
        # looks like just before close of master frame

    # "Private" Methods

    def __WriteBones(self, Bones):
        # Simply export the frames for each bone.  Export in rest position or
        # posed position depending on options.
        for Bone in Bones:
            BoneMatrix = Matrix()  # 4x4 identity matrix

            if self.config.ExportBonePosition == 'REST':
                if Bone.parent:
                    BoneMatrix = Bone.parent.matrix_local.inverted()
                BoneMatrix *= Bone.matrix_local
            elif self.config.ExportBonePosition == 'POSE':
                PoseBone = self.BlenderObject.pose.bones[Bone.name]
                if Bone.parent:
                    BoneMatrix = PoseBone.parent.matrix.inverted()
                BoneMatrix *= PoseBone.matrix

            BoneSafeName = self.SafeName + "_" + \
                Util.SafeName(Bone.name)
            self.__OpenBoneFrame(BoneSafeName, BoneMatrix)

            self.__WriteBoneChildren(Bone)

            self.__CloseBoneFrame(BoneSafeName)

    def __OpenBoneFrame(self, BoneSafeName, BoneMatrix):
        self.Exporter.File.Write("Frame frm-{} {{\n".format(BoneSafeName))
        self.Exporter.File.Indent()

        self.Exporter.File.Write("FrameTransformMatrix {\n")
        self.Exporter.File.Indent()
        Util.WriteMatrix(self.Exporter.File, BoneMatrix)
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")

        self.Exporter.File.Write("BoneInfo {\n")
        self.Exporter.File.Indent()
        self.Exporter.File.Write("\"{}\";\n" .format(BoneSafeName))
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")

        # somehow JointConstraint is here too

        self.Exporter.File.Write("AnimLinkName {\n")
        self.Exporter.File.Indent()
        self.Exporter.File.Write("\"{}\";\n" .format(BoneSafeName))
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")

    def __CloseBoneFrame(self, BoneSafeName):
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {}\n".format(BoneSafeName))

    def __WriteBoneChildren(self, Bone):
        self.__WriteBones(Util.SortByNameField(Bone.children))


# Bone object implementation of ExportObject
class BoneExportObject(ExportObject):
    def __init__(self, config, Exporter, BlenderObject, ParentArmature):
        ExportObject.__init__(self, config, Exporter, BlenderObject)

        self.ParentArmature = ParentArmature
        self.name = ParentArmature.name + '_' + self.BlenderObject.name
        self.type = 'BONE'
        self.SafeName = Util.SafeName(ParentArmature.name) + '_' + Util.SafeName(self.BlenderObject.name)

    def __repr__(self):
        return "[BoneExportObject: {}]".format(self.name)

    # "Public" Interface
    def Write(self):
        self._Write(self)

    # "Protected" Methods
    def _Write(self, Bone):
        self.Exporter.log.log("Opening frame for {}".format(self), False, True)
        self._OpenFrame()

        self.Exporter.log.log("Writing BoneInfo...", False, True)
        self.__WriteBone()
        self.Exporter.log.log("Done", False, True)

        self.Exporter.log.log("Writing children of {}".format(self), False, True)
        self._WriteChildren()
        self.Exporter.log.log("Done", False, True)

        self._CloseFrame()
        self.Exporter.log.log("Close frame of {}".format(self), False, True)

    def _MatrixCompute(self):
        Bone = self.BlenderObject
        MatrixArmature = self.ParentArmature
        print("Armature bone pose position", MatrixArmature, MatrixArmature.data.pose_position)
        self.config.ExportBonePosition = MatrixArmature.data.pose_position
        PoseBone = MatrixArmature.pose.bones[Bone.name]
        self.Matrix_local = MatrixArmature.matrix_world

        if self.config.ExportBonePosition == 'REST':
            if Bone.parent:
                self.Matrix_local = Bone.parent.matrix_local.inverted()
            self.Matrix_local = self.Matrix_local @ Bone.matrix_local
        elif self.config.ExportBonePosition == 'POSE':
            if Bone.parent:
                self.Matrix_local = PoseBone.parent.matrix.inverted()
            self.Matrix_local = self.Matrix_local @ PoseBone.matrix

    # "Private" methods
    def __WriteBone(self):
        self.Exporter.File.Write("BoneInfo {\n")
        self.Exporter.File.Indent()
        self.Exporter.File.Write("\"{}\";\n" .format(self.SafeName))
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")
        self.Exporter.File.Write("AnimLinkName {\n")
        self.Exporter.File.Indent()
        self.Exporter.File.Write("\"{}\";\n" .format(self.SafeName))
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")


# Container for animation data
class Animation:
    def __init__(self, SafeName):
        self.SafeName = SafeName
        self.AnimTag = None
        self.KeyRange = 0

        self.RotationKeys = {}
        self.PositionKeys = {}


# Creates a list of Animation objects based on the animation needs of the
# ExportObject passed to it
class AnimationGenerator:  # Base class, do not use
    def __init__(self, config, SafeName, ExportObject, modeldefTree):
        self.config = config
        self.SafeName = SafeName
        self.ExportObject = ExportObject
        self.modeldefTree = modeldefTree

        self.Animations = []


# Creates one Animation object that contains the rotation, scale, and position
# of the ExportObject
class GenericAnimationGenerator(AnimationGenerator):
    def __init__(self, config, SafeName, ExportObject, modeldefTree):
        AnimationGenerator.__init__(self, config, SafeName, ExportObject, modeldefTree)

        self._GenerateKeys()

    # "Protected" Interface

    def _GenerateKeys(self):
        # only gather keyframes from tagged objects
        if (not self.ExportObject.BlenderObject.fsx_anim_tag):
            return
        print("_GenerateKeys fsx_anim_tag", self.ExportObject.BlenderObject.fsx_anim_tag)
        Scene = bpy.context.scene  # Convenience alias
        BlenderCurrentFrame = Scene.frame_current
        Scene.frame_set(0)

        CurrentAnimation = Animation(self.ExportObject.SafeName)
        BlenderObject = self.ExportObject.BlenderObject
        CurrentAnimation.AnimTag = BlenderObject.fsx_anim_tag
        RotBase = BlenderObject.matrix_local.to_quaternion()
        PosBase = BlenderObject.matrix_local.to_translation()
        FCurves = None
        try:
            FCurves = BlenderObject.animation_data.action.fcurves
        except AttributeError:
            print("_GenerateKeys - Error no action fcurves", BlenderObject.fsx_anim_tag)
            pass


        # TODO: should check for NLATracks too? maybe aleady does


        # if there is a constraint applied to the object, we need to capture every frame
        if BlenderObject.constraints or not BlenderObject.animation_data:
            print("_GenerateKeys - animation tag", BlenderObject.fsx_anim_tag)
            modeldefRoot = self.modeldefTree.getroot()
            animtag = modeldefRoot.find(".Animation[@name='%s']" % (BlenderObject.fsx_anim_tag))
            # if defined, get framerange from modeldef (for most animations)
            framerange = 0
            try:
                framerange = int(animtag.attrib['length'])
            except KeyError:  # i.e. "Ambient" animations
                try:
                    for fcu in FCurves:
                        if framerange < fcu.range()[1]:
                            framerange = int(fcu.range()[1])
                except:
                    try:
                        framerange = int(BlenderObject.fsx_anim_length.split('-')[-1])
                    except:
                        raise ExportError("Couldn't determine length of animation!")
            CurrentAnimation.KeyRange = framerange

            for Frame in range(framerange + 1):
                Scene.frame_set(Frame)

                CurrentAnimation.RotationKeys[Frame] = BlenderObject.matrix_local.to_quaternion().rotation_difference(RotBase)
                CurrentAnimation.PositionKeys[Frame] = BlenderObject.matrix_local.to_translation() - PosBase

        # if there are no constraints applied to the object, just collect the keyframes
        elif FCurves is not None:
            print("_GenerateKeys - FCurves only", BlenderObject.fsx_anim_tag)
            for fcu in FCurves:
                KeyType = fcu.data_path
                # check correct type and that we don't already have keyframes of that type
                if (KeyType not in ['location', 'rotation_euler']):
                    continue

                # collect keyframe data
                for KeyFrame in fcu.keyframe_points:
                    Frame = int(KeyFrame.co[0])  # Changed to explicit conversion to int, due to 3.1 API changes https://wiki.blender.org/wiki/Reference/Release_Notes/3.1/Python_API  Dave_W
                    if Frame not in CurrentAnimation.RotationKeys.keys():
                        Scene.frame_set(Frame)
                        CurrentAnimation.PositionKeys[Frame] = BlenderObject.matrix_local.to_translation() - PosBase
                        CurrentAnimation.RotationKeys[Frame] = BlenderObject.matrix_local.to_quaternion().rotation_difference(RotBase)

                if fcu.range()[1] > CurrentAnimation.KeyRange:
                    CurrentAnimation.KeyRange = fcu.range()[1]

        if CurrentAnimation.KeyRange > 0:
            self.Animations.append(CurrentAnimation)
        Scene.frame_set(BlenderCurrentFrame)


# Creates an Animation object for the ArmatureExportObject it gets passed and
# an Animation object for each bone in the armature (if options allow)
# looks like this function is never called -  no other references in the py files.
class ArmatureAnimationGenerator(GenericAnimationGenerator):
    def __init__(self, config, SafeName, ArmatureExportObject, modeldefTree):
        GenericAnimationGenerator.__init__(self, config, SafeName,
                                           ArmatureExportObject, modeldefTree)

        if self.config.ExportSkinWeights:
            self._GenerateBoneKeys()

    # "Protected" Interface

    def _GenerateBoneKeys(self):
        from itertools import zip_longest as zip

        Scene = bpy.context.scene  # Convenience alias
        BlenderCurrentFrame = Scene.frame_current
        Scene.frame_set(0)

        ArmatureObject = self.ExportObject.BlenderObject
        ArmatureSafeName = self.ExportObject.SafeName

        AnimatedBones = [Bone for Bone in ArmatureObject.pose.bones
                         if ArmatureObject.data.bones[Bone.name].fsx_anim_tag]

        for Bone in AnimatedBones:
            for fcu in ArmatureObject.animation_data.action.fcurves:
                if Bone.name == fcu.data_path.split('"')[1]:
                    Keytype = fcu.data_path.split('"')[2][2:]

        root = self.modeldefTree.getroot()
        # Create Animation objects for each bone
        BoneAnimations = [Animation(ArmatureSafeName + "_" + \
                          Util.SafeName(Bone.name)) for Bone in AnimatedBones]

        framerange = 0
        for Bone, BoneAnimation in zip(AnimatedBones, BoneAnimations):
            animtag = root.find(".Animation[@name='%s']" % (ArmatureObject.data.bones[Bone.name].fsx_anim_tag))
            BoneAnimation.AnimTag = ArmatureObject.data.bones[Bone.name].fsx_anim_tag
            try:
                framerange = int(animtag.attrib['length'])
            except KeyError:
                for fcu in ArmatureObject.animation_data.action.fcurves:
                    if fcu.data_path.split('"')[1] == Bone.name:
                        if framerange < fcu.range()[1]:
                            framerange = int(fcu.range()[1])
            BoneAnimation.KeyRange = framerange

        for Frame in range(framerange + 1):
            Scene.frame_set(Frame)

            for Bone, BoneAnimation in zip(AnimatedBones, BoneAnimations):

                RestBone = ArmatureObject.data.bones[Bone.name]
                if Bone.parent:
                    PoseMatrix = Bone.parent.matrix.inverted() @ Bone.matrix
                    LocVector = RestBone.head_local - RestBone.parent.head_local
                else:
                    PoseMatrix = RestBone.matrix_local.inverted() @ Bone.matrix
                    LocVector = RestBone.head_local

                Rotation = PoseMatrix.to_quaternion()
                Rotation.conjugate()
                Position = PoseMatrix.to_translation()
                yPos = Position[1]
                Position[1] = Position[2]
                Position[2] = yPos
                Position -= LocVector

                BoneAnimation.RotationKeys[Frame] = Rotation
                BoneAnimation.PositionKeys[Frame] = Position

        self.Animations += BoneAnimations
        Scene.frame_set(BlenderCurrentFrame)


class BoneAnimationGenerator(AnimationGenerator):
    def __init__(self, config, SafeName, BoneExportObject, modeldefTree):
        AnimationGenerator.__init__(self, config, SafeName,
                                    BoneExportObject, modeldefTree)

        if self.config.ExportSkinWeights:
            self._GenerateBoneKeys()

    # "Protected" Interface
    def _GenerateBoneKeys(self):
        Bone = self.ExportObject.BlenderObject
        if not Bone.fsx_anim_tag:
            return
        print("_GenerateBoneKeys found animation tag", Bone.fsx_anim_tag)
        Scene = bpy.context.scene
        BlenderCurrentFrame = Scene.frame_current
        Scene.frame_set(0)

        Armature = self.ExportObject.ParentArmature
        PoseBone = Armature.pose.bones[Bone.name]
        BoneAnimation = Animation(self.ExportObject.SafeName)
        BoneAnimation.AnimTag = Bone.fsx_anim_tag
        if PoseBone.parent:
            Matrix_base = PoseBone.parent.matrix.inverted() @ PoseBone.matrix
        else:
            Matrix_base = PoseBone.matrix
        Quaternion_base = Matrix_base.to_quaternion()
        Translation_base = Matrix_base.to_translation()

        if PoseBone.constraints:
            print("_GenerateBoneKeys - PoseBone.Constraints", PoseBone.constraints)
            root = self.modeldefTree.getroot()
            animtag = root.find(".Animation[@name='%s']" % (Bone.fsx_anim_tag))
            try:
                framerange = int(animtag.attrib['length'])
            except KeyError:
                print("_GenerateBoneKeys KeyError")
                for fcu in Armature.animation_data.action.fcurves:
                    if fcu.data_path.split('"')[1] == Bone.name:
                        if framerange < fcu.range()[1]:
                            framerange = int(fcu.range()[1])
            BoneAnimation.KeyRange = framerange

            print("_GenerateBoneKeys PoseBone", PoseBone)
            for Frame in range(framerange + 1):
                print("_GenerateBoneKeys - Pose constraint Frame Loop", Frame)
                Scene.frame_set(int(Frame))

                if PoseBone.parent:
                    PoseMatrix = PoseBone.parent.matrix.inverted() @ PoseBone.matrix
                else:
                    PoseMatrix = PoseBone.matrix

                Rotation = -1 * Quaternion_base.rotation_difference(PoseMatrix.to_quaternion())
                Rotation.conjugate()
                Position = PoseMatrix.to_translation() - Translation_base

                BoneAnimation.RotationKeys[Frame] = Rotation
                BoneAnimation.PositionKeys[Frame] = Position
        elif (Armature.animation_data is not None):   # added to catch error
            if Armature.animation_data.action is not None:
                print("_GenerateBoneKeys - Armature.animation_data.action.fcurves")
                for fcu in Armature.animation_data.action.fcurves:
                    try:
                        if Bone.name != fcu.data_path.split('"')[1]:
                            continue
                    except IndexError:
                        continue
                    else:
                        KeyType = fcu.data_path.split('"')[2][2:]

                        if KeyType not in ['rotation_quaternion', 'location']:
                            continue

                        print("_GenerateBoneKeys - Bonename", Bone.name)
                        for KeyFrame in fcu.keyframe_points:
                            Frame = KeyFrame.co[0]
                            if Frame not in BoneAnimation.RotationKeys.keys():
                                print("_GenerateBoneKeys - Frame", Frame)
                                Scene.frame_set(int(Frame))
                                Rotation = PoseBone.matrix_basis.to_quaternion()
                                Rotation.conjugate()
                                Position = PoseBone.matrix_basis.to_translation()
                                Position = Matrix_base.to_3x3() @ Position

                                BoneAnimation.RotationKeys[Frame] = Rotation
                                BoneAnimation.PositionKeys[Frame] = Position

                    if fcu.range()[1] > BoneAnimation.KeyRange:
                        BoneAnimation.KeyRange = fcu.range()[1]
            else:
                print("BoneAnimationGenerator - skipped Armature Bones Keys no action - check NLAs", Armature, Armature.animation_data, Armature.animation_data.nla_tracks )
                for nlatrack in Armature.animation_data.nla_tracks:
                    if not nlatrack.mute:
                        print("BoneAnimationGenerator - NLATrack Name", nlatrack.name, nlatrack.strips)
                        for strip in nlatrack.strips:
                            print("BoneAnimationGenerator - NLATrack strip", strip.name)
                            for fcu in strip.action.fcurves:
                                try:
                                    if Bone.name != fcu.data_path.split('"')[1]:
                                        continue
                                except IndexError:
                                    continue
                                else:
                                    KeyType = fcu.data_path.split('"')[2][2:]

                                    if KeyType not in ['rotation_quaternion', 'location']:
                                        continue

                                    print("_GenerateBoneKeys - Bonename", Bone.name)
                                    for KeyFrame in fcu.keyframe_points:
                                        Frame = KeyFrame.co[0]
                                        if Frame not in BoneAnimation.RotationKeys.keys():
                                            print("_GenerateBoneKeys - Frame NLATrack strip", Frame)
                                            Scene.frame_set(int(Frame)) # int correct here
                                            Rotation = PoseBone.matrix_basis.to_quaternion()
                                            Rotation.conjugate()
                                            Position = PoseBone.matrix_basis.to_translation()
                                            Position = Matrix_base.to_3x3() @ Position

                                            BoneAnimation.RotationKeys[Frame] = Rotation
                                            BoneAnimation.PositionKeys[Frame] = Position

                                if fcu.range()[1] > BoneAnimation.KeyRange:
                                    BoneAnimation.KeyRange = fcu.range()[1]
        else:
            print("BoneAnimationGenerator - skipped Armature Bones Keys no data", Armature, Armature.animation_data)
        if BoneAnimation.KeyRange > 0:
            self.Animations.append(BoneAnimation)
        Scene.frame_set(BlenderCurrentFrame)
