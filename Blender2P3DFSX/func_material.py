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
# but with an updated UI and compatibility for Blender 3.3.x. Parts of the
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
from . environment import *


class MaterialError(Exception):
    def __init__(self, msg, objs=None):
        self.msg = msg
        self.objs = objs


class MaterialUtil():

    def MakeOpaque(Material):
        Material.blend_method = 'OPAQUE'

    def MakeMasked(Material):
        Material.blend_method = 'BLEND'
        Material.use_backface_culling = True

    def MakeTranslucent(Material):
        Material.blend_method = 'BLEND'
        Material.use_backface_culling = True

    def MakeAdditive(Material):
        Material.blend_method = 'BLEND'
        Material.use_backface_culling = True
        
    def CreateSpecShader(Material):
        # Deleted RemoveShaderNodes function to allow location control of spec_shader_node and output_node. 20-02-2023     Dave_W
        name = bpy.context.active_object.active_material.name
        material = bpy.data.materials.get(name)
        material.use_nodes = True
        nodes = Material.node_tree.nodes
        links = Material.node_tree.links
        for idx, node in enumerate(nodes):
            print("Deleting: %s | %s" % (node.name, node.type))
            nodes.remove(node)

        def CreateNewNode(Material, node_type, label=None, location=(.0, .0)):
            new_node = None
            try:
                new_node = Material.node_tree.nodes.new(node_type)
                if label is not None:
                    new_node.name = label
                    new_node.label = label
                new_node.location = location
            finally:
                print("New node of type '%s' created for material '%s'." % (node_type, Material.name))

            if new_node is None:
                msg = format("MATERIAL ERROR! A new output shader node could not be created for the material '%s'." % Material.name)
                raise MaterialError(msg)
            return new_node

        def CreateAlpha(Material):
            value_node = None
            math_node = None
            links = Material.node_tree.links
            try:
                value_node = Material.node_tree.nodes.new('ShaderNodeValue')
                value_node.name = "Alpha Value"
                value_node.label = "Alpha Value"
                value_node.location = location=(-650, 1040)
                value_node.outputs[0].default_value = 1.0
            finally:
                pass

            try:
                math_node = Material.node_tree.nodes.new('ShaderNodeMath')
                math_node.name = "One Minus Alpha"
                math_node.label = "One Minus Alpha"
                math_node.operation = "SUBTRACT"
                math_node.location = location=(-450, 1040)
                math_node.inputs[0].default_value = 1.0
            finally:
                pass

            links.new(value_node.outputs[0], math_node.inputs[1])
            return math_node

        #nodes = Material.node_tree.nodes

        output_node = None

        # check if there is an output node, create one if not:
        if output_node is None:
            output_node = CreateNewNode(Material, 'ShaderNodeOutputMaterial', location=(500, 0))

        # Create the specular BSDF shader node:
        spec_shader_node = CreateNewNode(Material, 'ShaderNodeEeveeSpecular', location=(300, 0))
        spec_shader_node.inputs["Clear Coat"].hide = True   # hide Clear Coat sockets not used for specular workflow Dave_W
        spec_shader_node.inputs["Clear Coat Roughness"].hide = True
        spec_shader_node.inputs["Clear Coat Normal"].hide = True
        # set to 1.0 inverse of alpha = 0.0 - seems diffuse color alpha should not be used to set alpha - only when we have a texture - NOPE setting to 1 makes all black render.
        # spec_shader_node.inputs["Transparency"].default_value = 1.0

        # Create the base color Diffuse texture
        base_color_texture_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Diffuse", location=(-1000, 640))
        # ToDo: specular diffuse color node needed

        # ToDo: PBR albedo color node needed
        # create the base color node: added ronh
        diffuse_color_node = CreateNewNode(Material, 'ShaderNodeRGB', "Diffuse Color", location=(-850, 1040))
        diffuse_color_node.outputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
        diffuse_color_blend_node = CreateNewNode(Material, 'ShaderNodeMixRGB', "Diffuse Color Blend", location=(-350, 760))
        diffuse_color_blend_node.blend_type = 'MULTIPLY'
        diffuse_color_blend_node.inputs["Fac"].default_value = 1.0
        diffuse_color_blend_node.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
        math_node = CreateAlpha(Material)
        specular_color_node = CreateNewNode(Material, 'ShaderNodeRGB', "Specular Color", location=(-475, -140))
        specular_color_blend_node = CreateNewNode(Material, 'ShaderNodeMixRGB', "Specular Color Blend", location=(-275, -20))
        specular_color_blend_node.blend_type = 'MULTIPLY'
        specular_color_blend_node.inputs["Fac"].default_value = 1.0
        specular_color_blend_node.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
        emissive_color_node = CreateNewNode(Material, 'ShaderNodeRGB', "Emissive Color", location=(-475, -460))
        emissive_color_blend_node = CreateNewNode(Material, 'ShaderNodeMixRGB', "Emissive Color Blend", location=(-275, -460))
        emissive_color_blend_node.blend_type = 'MULTIPLY'
        emissive_color_blend_node.inputs["Fac"].default_value = 1.0
        emissive_color_blend_node.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)

        # ToDo: Specular - Specular Level nodes needed - specular factor or Power???  (Glossiness and Soften is not used???)
        # Specular nodes
        power_node = CreateNewNode(Material, 'ShaderNodeValue', "Power Factor", location=(-470, -50))

        # create the detail maps nodes:
        detail_scale_node = CreateNewNode(Material, 'ShaderNodeMapping', 'Detail Scale', location=(-1250, 300))

        texture_detail_map_node = CreateNewNode(Material, 'ShaderNodeTexImage', 'Detail', location=(-1000, 280))

        # put Detail Scale and Detail nodes in frame:       Dave_W
        detail_nodes_frame = nodes.new(type='NodeFrame')
        detail_nodes_frame.label = 'Detail'
        detail_scale_node.parent = detail_nodes_frame
        texture_detail_map_node.parent = detail_nodes_frame

        detail_blend_node = CreateNewNode(Material, 'ShaderNodeMixRGB', 'Detail Blend', location=(-150, 375))
        detail_blend_node.blend_type = 'OVERLAY'
        detail_blend_node.inputs["Fac"].default_value = 0

        # transparency
        inv_alpha_node = CreateNewNode(Material, 'ShaderNodeInvert', "Transparency", location=(-500, 200))

        # specular color texture
        spec_color_texture_node = CreateNewNode(Material, 'ShaderNodeTexImage', "specular", location=(-1000, -120))     # "specular" name cannot be capitalized. Node will not connect to BSDF shader.  Dave_W

        # create the emission node:
        emission_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Emissive", location=(-1000, -420))

        # create the normal map nodes:
        bump_scale_node = CreateNewNode(Material, 'ShaderNodeMapping', 'Bump Scale', location=(-1250, -770))
        texture_normal_map_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Normal", location=(-1000, -770))
        sep_rgb_node = CreateNewNode(Material, 'ShaderNodeSeparateRGB', location=(-700, -770))
        sep_rgb_node.outputs["R"].hide = True
        com_rgb_node = CreateNewNode(Material, 'ShaderNodeCombineRGB', location=(-500, -770))
        mix_normal_node = CreateNewNode(Material, 'ShaderNodeMixRGB', "Mix Normals", location=(-300, -770))
        normal_map_node = CreateNewNode(Material, 'ShaderNodeNormalMap', location=(-100, -770))
        normal_map_node.inputs["Strength"].default_value = 0

        # put normal map nodes in frame:        Dave_W
        specular_normal_frame = nodes.new(type='NodeFrame')
        specular_normal_frame.label = 'Normal Map'
        bump_scale_node.parent = specular_normal_frame
        sep_rgb_node.parent = specular_normal_frame
        com_rgb_node.parent = specular_normal_frame
        mix_normal_node.parent = specular_normal_frame
        normal_map_node.parent = specular_normal_frame

        # flip image nodes:
        uv_node = CreateNewNode(Material, 'ShaderNodeUVMap', "UV", location=(-2000, 0))

        # connect the nodes:
        # 22/01/23 reversed the order of connections e.g., outputs on left, inputs on right of statement.    Dave_W

        # ToDo: redo default links when no textures are added, this requires the Diffuse Color, and Albedo color nodes
        # the metallic factors, smoothness factor (1 - Roughness), Specular level, Glossiness and Soften
        # see the P3D SDK Modeling Materials, PBR Materilas sections, References/variables/Material Variables

        links.new(spec_shader_node.outputs["BSDF"], output_node.inputs["Surface"])

        links.new(base_color_texture_node.outputs["Color"], detail_blend_node.inputs["Color1"])

        links.new(base_color_texture_node.outputs["Alpha"], inv_alpha_node.inputs["Color"])

        #move to update
        #links.new(detail_blend_node.outputs["Color"], spec_shader_node.inputs["Base Color"])
        # remove this - causes wrong color in render grey should be black issue
        #links.new(math_node.outputs["Value"], spec_shader_node.inputs["Transparency"])

        links.new(diffuse_color_node.outputs["Color"], diffuse_color_blend_node.inputs["Color1"])
        links.new(diffuse_color_blend_node.outputs["Color"], spec_shader_node.inputs["Base Color"])

        # connect detail texture map
        links.new(texture_detail_map_node.outputs["Color"], detail_blend_node.inputs["Color2"])
        links.new(detail_scale_node.outputs["Vector"], texture_detail_map_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], detail_scale_node.inputs["Vector"])

        # move to update
        #links.new(spec_color_texture_node.outputs["Color"], spec_shader_node.inputs["Specular"])

        links.new(specular_color_blend_node.outputs["Color"], spec_shader_node.inputs["Specular"])
        links.new(specular_color_node.outputs["Color"], specular_color_blend_node.inputs["Color1"])
        links.new(power_node.outputs["Value"], specular_color_blend_node.inputs["Fac"])

        links.new(emissive_color_blend_node.outputs["Color"], spec_shader_node.inputs["Emissive Color"])
        links.new(emissive_color_node.outputs["Color"], emissive_color_blend_node.inputs["Color1"])


        links.new(texture_normal_map_node.outputs["Color"], sep_rgb_node.inputs["Image"])
        links.new(texture_normal_map_node.outputs["Alpha"], com_rgb_node.inputs["R"])
        links.new(sep_rgb_node.outputs["G"], com_rgb_node.inputs["G"])
        links.new(sep_rgb_node.outputs["B"], com_rgb_node.inputs["B"])
        links.new(com_rgb_node.outputs["Image"], mix_normal_node.inputs["Color2"])
        links.new(texture_normal_map_node.outputs["Color"], mix_normal_node.inputs["Color1"])
        links.new(mix_normal_node.outputs["Color"], normal_map_node.inputs["Color"])
        # move to update
        #links.new(normal_map_node.outputs["Normal"], spec_shader_node.inputs["Normal"])

        # connect flip image to image:
        links.new(uv_node.outputs["UV"], base_color_texture_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], spec_color_texture_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], emission_node.inputs["Vector"])
        links.new(bump_scale_node.outputs["Vector"], texture_normal_map_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], bump_scale_node.inputs["Vector"])

    def CreatePBRShader(Material):
        # Deleted RemoveShaderNodes function to allow location control of spec_shader_node and output_node. 20-02-2023     Dave_W
        name = bpy.context.active_object.active_material.name
        material = bpy.data.materials.get(name)
        material.use_nodes = True
        nodes = Material.node_tree.nodes
        for idx, node in enumerate(nodes):
            print("Deleting: %s | %s" % (node.name, node.type))
            nodes.remove(node)

        def FindNodeByType(node_type):
            for idx, node in enumerate(nodes):
                if node.type == node_type:
                    return node
            return None

        def FindNodeByName(node_name):
            for idx, node in enumerate(nodes):
                if node.name == node_name:
                    return node
            return None

        def CreateNewNode(Material, node_type, label=None, location=(.0, .0)):
            new_node = None
            try:
                new_node = Material.node_tree.nodes.new(node_type)
                if label is not None:
                    new_node.name = label
                    new_node.label = label
                new_node.location = location
            finally:
                print("New node '%s' of type '%s' created for material '%s'." % (new_node.name, node_type, Material.name))

            if new_node is None:
                msg = format("MATERIAL ERROR! A new output shader node could not be created for the material '%s'." % Material.name)
                raise MaterialError(msg)
            return new_node

        def CreateAlpha(Material):
            value_node = None
            links = Material.node_tree.links
            try:
                value_node = Material.node_tree.nodes.new('ShaderNodeValue')
                value_node.name = "Alpha Value"
                value_node.label = "Alpha Value"
                value_node.location = location=(-850, 1040)
                value_node.outputs[0].default_value = 1.0
            finally:
                pass

            return value_node

        nodes = Material.node_tree.nodes
        links = Material.node_tree.links

        output_node = None

        # check if there is an output node, create one if not:
        if output_node is None:
            output_node = CreateNewNode(Material, 'ShaderNodeOutputMaterial', location=(500, 100))

        # create the main BSDF node:
        bsdf_node = CreateNewNode(Material, 'ShaderNodeBsdfPrincipled', location=(200, 100))

        # create the base color texture node: renamed ronh
        base_color_texture_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Albedo", location=(-1150, 900))

        # ToDo: PBR albedo color node needed
        # create the base color node: added ronh
        base_color_node = CreateNewNode(Material, 'ShaderNodeRGB', "Base Color", location=(-850, 1240))
        base_color_node.outputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
        alpha_value_node = CreateAlpha(Material)
        base_color_mix_node = CreateNewNode(Material, 'ShaderNodeMixRGB', "Base Color Mix", location=(-650, 760))
        base_color_mix_node.blend_type = 'MULTIPLY'
        base_color_mix_node.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1.0)
        base_color_mix_node.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
        base_color_mix_node.inputs["Fac"].default_value = 1.0


        # create the detail maps nodes
        detail_scale_node = CreateNewNode(Material, 'ShaderNodeMapping', 'Detail Scale', location=(-1650, 300))

        texture_detail_map_node = CreateNewNode(Material, 'ShaderNodeTexImage', 'Detail', location=(-1450, 280))

        # put Detail Scale and Detail nodes in frame:       Dave_W
        detail_nodes_frame = nodes.new(type='NodeFrame')
        detail_nodes_frame.label = 'Detail'
        detail_scale_node.parent = detail_nodes_frame
        texture_detail_map_node.parent = detail_nodes_frame

        detail_blend_node = CreateNewNode(Material, 'ShaderNodeMixRGB', 'Detail Blend', location=(-400, 500))
        detail_blend_node.blend_type = 'OVERLAY'
        detail_blend_node.inputs["Fac"].default_value = 0

        # ToDo: PBR metallic scale and smoothness scale (1 - Roughness) nodes needed

        # create the metallic/smoothness/occlusion texture and operation
        texture_metallic_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Metallic", location=(-1450, -150))
        metallic_factor_node = CreateNewNode(Material, 'ShaderNodeValue', "Metallic Factor", location=(-850, -50))
        rgb_separate_node = CreateNewNode(Material, 'ShaderNodeSeparateRGB', "Separate Red", location=(-850, -150))
        #rgb_separate_node.outputs["G"].hide = True
        #rgb_separate_node.outputs["B"].hide = True

        # create an inverse for the smoothness/roughness input:
        #math_node_smoothness = CreateNewNode(Material, 'ShaderNodeInvert', "Metallic Roughness", location=(-850, -310))
        #math_node_smoothness.inputs["Fac"].default_value = 1
        smoothness_factor_node = CreateNewNode(Material, 'ShaderNodeValue', "Smoothness Factor", location=(-850, -440))
        smoothness_math_node = CreateNewNode(Material, 'ShaderNodeMath', "Invert 1 minus", location=(-550, -210))
        smoothness_math_node.operation = 'SUBTRACT'
        smoothness_math_node.inputs[0].default_value = 1.0
        smoothness_math_node.use_clamp = True

        # put metallic nodes in frame:        Dave_W
        metallic_frame = nodes.new(type='NodeFrame')
        metallic_frame.label = 'Metallic'
        texture_metallic_node.parent = metallic_frame
        rgb_separate_node.parent = metallic_frame
        #math_node_smoothness.parent = metallic_frame
        smoothness_math_node.parent = metallic_frame
        smoothness_factor_node.parent = metallic_frame
        metallic_factor_node.parent = metallic_frame

        # create the emission node:
        emission_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Emissive", location=(-1450, -480))

        # create the normal map nodes:
        bump_scale_node = CreateNewNode(Material, 'ShaderNodeMapping', 'Bump Scale', location=(-1650, -810))
        texture_normal_map_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Normal", location=(-1450, -810))
        sep_rgb_node = CreateNewNode(Material, 'ShaderNodeSeparateRGB', "Separate GB", location=(-1100, -810))
        sep_rgb_node.outputs["R"].hide = True
        com_rgb_node = CreateNewNode(Material, 'ShaderNodeCombineRGB', "Combine Color", location=(-850, -810))
        mix_normal_node = CreateNewNode(Material, 'ShaderNodeMixRGB', "Mix Normals", location=(-670, -810))
        normal_map_node = CreateNewNode(Material, 'ShaderNodeNormalMap', location=(-350, -810))
        normal_map_node.inputs["Strength"].default_value = 0

        # put normal map nodes in frame:        Dave_W
        pbr_normalframe = nodes.new(type='NodeFrame')
        pbr_normalframe.label = 'Normal Map'
        bump_scale_node.parent = pbr_normalframe
        sep_rgb_node.parent = pbr_normalframe
        com_rgb_node.parent = pbr_normalframe
        mix_normal_node.parent = pbr_normalframe
        normal_map_node.parent = pbr_normalframe

        # create the Clearcoat nodes:                  Dave_W
        texture_clear_coat_node = CreateNewNode(Material, 'ShaderNodeTexImage', "Clearcoat", location=(-1450, -1260))
        sep_color_node = CreateNewNode(Material, 'ShaderNodeSeparateColor', "CC Separate Color", location=(-1100, -1260))
        cc_node_smoothness = CreateNewNode(Material, 'ShaderNodeInvert', "Clearcoat Roughness", location=(-850, -1260))
        cc_node_smoothness.inputs["Fac"].default_value = 1
        cc_com_rgb_node = CreateNewNode(Material, 'ShaderNodeCombineRGB', "CC Combine ColorRGB", location=(-850, -1390))
        cc_mix_normal_node = CreateNewNode(Material, 'ShaderNodeMixRGB', "CC Mix Normals", location=(-670, -1260))
        cc_normal_map_node = CreateNewNode(Material, 'ShaderNodeNormalMap', "CC Normal Map", location=(-350, -1260))
        cc_normal_map_node.inputs["Strength"].default_value = 0

        # put Clearcoat nodes in frame:        Dave_W
        clearcoat_frame = nodes.new(type='NodeFrame')
        clearcoat_frame.label = 'Clearcoat'
        texture_clear_coat_node.parent = clearcoat_frame
        sep_color_node.parent = clearcoat_frame
        cc_node_smoothness.parent = clearcoat_frame
        cc_com_rgb_node.parent = clearcoat_frame
        cc_mix_normal_node.parent = clearcoat_frame
        cc_normal_map_node.parent = clearcoat_frame

        # flip image nodes:
        uv_node = CreateNewNode(Material, 'ShaderNodeUVMap', "UV", location=(-3000, 0))

        # connect the nodes:
        # 22/01/23 reversed the order of connections e.g., outputs on left, inputs on right of statement.    Dave_W

        # ToDo: redo default links when no textures are added, this requires the Diffuse Color, and Albedo color nodes
        # the metallic factors, smoothness factor (1 - Roughness), Specular level, Glossiness and Soften
        # see the P3D SDK Modeling Materials, PBR Materilas sections, References/variables/Material Variables

        # ToDo: rework this so the color nodes are added and mix nodes etc. Like MSFS
        # Base color albedo, specular color, diffuse color, specular level scale (Power), metallic scale, smoothness scale, emissive color
        # BSDF
        links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])
        # ToDo: move to base color texture update
        #links.new(base_color_texture_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])

        # detail texture map
        # ToDo: move to detail/base color texture update
        #links.new(detail_blend_node.outputs["Color"], bsdf_node.inputs["Base Color"])
        # keep
        links.new(base_color_node.outputs["Color"], base_color_mix_node.inputs["Color2"]) # added ronh
        links.new(alpha_value_node.outputs["Value"], bsdf_node.inputs["Alpha"])
        links.new(base_color_mix_node.outputs["Color"], detail_blend_node.inputs["Color1"])
        links.new(base_color_mix_node.outputs["Color"], bsdf_node.inputs["Base Color"])
        links.new(texture_detail_map_node.outputs["Color"], detail_blend_node.inputs["Color2"])
        links.new(detail_scale_node.outputs["Vector"], texture_detail_map_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], detail_scale_node.inputs["Vector"])

        # metallic
        # keep
        links.new(texture_metallic_node.outputs["Color"], rgb_separate_node.inputs["Image"])
        #links.new(texture_metallic_node.outputs["Alpha"], math_node_smoothness.inputs["Color"])
        links.new(smoothness_factor_node.outputs["Value"], smoothness_math_node.inputs[1]) # added ronh second Value input for 1 minus
        links.new(metallic_factor_node.outputs["Value"], bsdf_node.inputs["Metallic"]) # added ronh
        links.new(smoothness_math_node.outputs["Value"], bsdf_node.inputs["Roughness"]) # added ronh
        # ToDo: move to update metallic texture
        #links.new(rgb_separate_node.outputs["R"], bsdf_node.inputs["Metallic"])
        #links.new(math_node_smoothness.outputs["Color"], bsdf_node.inputs["Roughness"])

        # normal
        # ToDo: normal update
        #links.new(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])
        # keep
        links.new(texture_normal_map_node.outputs["Color"], sep_rgb_node.inputs["Image"])
        links.new(texture_normal_map_node.outputs["Alpha"], com_rgb_node.inputs["R"])
        links.new(texture_normal_map_node.outputs["Color"], mix_normal_node.inputs["Color1"])
        links.new(sep_rgb_node.outputs["G"], com_rgb_node.inputs["G"])
        links.new(sep_rgb_node.outputs["B"], com_rgb_node.inputs["B"])
        links.new(com_rgb_node.outputs["Image"], mix_normal_node.inputs["Color2"])
        links.new(mix_normal_node.outputs["Color"], normal_map_node.inputs["Color"])

        # clearcoat             Dave_W
        # ToDo: add to clearcoat update
        #links.new(sep_color_node.outputs["Red"], bsdf_node.inputs["Clearcoat"])
        #links.new(cc_node_smoothness.outputs["Color"], bsdf_node.inputs["Clearcoat Roughness"])
        #links.new(cc_normal_map_node.outputs["Normal"], bsdf_node.inputs["Clearcoat Normal"])
        #keep
        links.new(texture_clear_coat_node.outputs["Color"], sep_color_node.inputs["Color"])
        links.new(sep_color_node.outputs["Green"], cc_node_smoothness.inputs["Color"])
        links.new(texture_clear_coat_node.outputs["Alpha"], cc_com_rgb_node.inputs["G"])
        links.new(sep_color_node.outputs["Blue"], cc_com_rgb_node.inputs["R"])
        links.new(sep_color_node.outputs["Blue"], cc_mix_normal_node.inputs["Color1"])
        links.new(cc_com_rgb_node.outputs["Image"], cc_mix_normal_node.inputs["Color2"])
        links.new(cc_mix_normal_node.outputs["Color"], cc_normal_map_node.inputs["Color"])

        # connect flip image to image:
        links.new(uv_node.outputs["UV"], base_color_texture_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], texture_metallic_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], emission_node.inputs["Vector"])
        links.new(bump_scale_node.outputs["Vector"], texture_normal_map_node.inputs["Vector"])
        links.new(uv_node.outputs["UV"], bump_scale_node.inputs["Vector"])

        # connect UV node UV socket to Clearcoat Vector socket      Dave_W
        links.new(uv_node.outputs["UV"], texture_clear_coat_node.inputs["Vector"])
