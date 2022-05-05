import os, subprocess

import datamodel as dmx
import asset, constants, halfedge_mesh, hp_ents

class T3dType:
	force_regen = False
	file_extension = "t3d"
	category = "map"

# Kind of a hack?
# Remember to fix the AssetDescription parameters check when this is fixed
class FlattenedTexturesType:
	force_regen = False
	file_extension = ""
	category = "flattened_textures"

class ObjType:
	force_regen = False
	file_extension = "obj"
	category = "map"

	@staticmethod
	def resolve_dependencies(obj_desc, t3d_desc):
		obj_desc.add_dependency_on(t3d_desc)

	@staticmethod
	def regenerate(obj_desc, t3d_desc):
		flattened_textures_dir = asset.AssetDescription(
			stage="intermediate",
			game=obj_desc.game,
			subfolder="",
			name="",
			asset_type=FlattenedTexturesType
		)
		subprocess.run([
			constants.T3D_TO_OBJ_PATH,
			"--post-scale",
			str(constants.T3D_SCALE * constants.SCALE),
			t3d_desc.path(),
			flattened_textures_dir.path()
		])
		output_path = t3d_desc.path()[:-3] + ObjType.file_extension
		if os.path.isfile(obj_desc.path()):
			os.remove(obj_desc.path())
		os.rename(output_path, obj_desc.path())

		script_path = os.path.realpath("blender_clean_obj.py")
		print("Starting Blender...")
		subprocess.run([constants.BLENDER_PATH,	"-b", "--python", script_path, "--", obj_desc.path()])

class VmapType:
	force_regen = False
	file_extension = "vmap"
	category = "map"

	@staticmethod
	def resolve_dependencies(vmap_desc, t3d_desc):
		vmap_desc.add_dependency_on(t3d_desc)
		obj_desc = t3d_desc.clone()
		obj_desc.stage = "intermediate"
		obj_desc.asset_type = ObjType
		obj_desc.resolve_dependencies(t3d_desc)
		vmap_desc.add_dependency_on(obj_desc)

	@staticmethod
	def get_mesh_data(dm, mesh: halfedge_mesh.Mesh):
		data = dm.add_element("meshData", "CDmePolygonMesh")

		def dmx_array(l):
			array_type = type(l[0])
			if issubclass(array_type, list) or issubclass(array_type, tuple):
				length = len(l[0])
				if length == 2:
					array_type = dmx.Vector2
				elif length == 3:
					array_type = dmx.Vector3
				elif length == 4:
					array_type = dmx.Vector4
				else:
					raise ValueError("Invalid vector length for " + str(l[0]))
				l = [array_type(i) for i in l]
			ret = dmx.make_array(None, array_type)
			ret.extend(l)
			return ret

		data["vertexEdgeIndices"] = dmx_array(mesh.vertex_edge_indices())
		data["vertexDataIndices"] = dmx_array(mesh.vertex_data_indices())
		data["edgeVertexIndices"] = dmx_array(mesh.edge_vertex_indices())
		data["edgeOppositeIndices"] = dmx_array(mesh.edge_opposite_indices())
		data["edgeNextIndices"] = dmx_array(mesh.edge_next_indices())
		data["edgeFaceIndices"] = dmx_array(mesh.edge_face_indices())
		data["edgeDataIndices"] = dmx_array(mesh.edge_data_indices())
		data["edgeVertexDataIndices"] = dmx_array(mesh.edge_vertex_data_indices())
		data["faceEdgeIndices"] = dmx_array(mesh.face_edge_indices())
		data["faceDataIndices"] = dmx_array(mesh.face_data_indices())

		data["materials"] = dmx_array(mesh.materials())

		def dmx_meshdata_stream(dm, name, attr_name, sem_name, flags, data):
			stream = dm.add_element(name, "CDmePolygonMeshDataStream")
			stream["standardAttributeName"] = attr_name
			stream["semanticName"] = sem_name
			stream["semanticIndex"] = 0
			stream["vertexBufferLocation"] = 0
			stream["dataStateFlags"] = flags
			stream["subdivisionBinding"] = None
			stream["data"] = dmx_array(data)

			return stream

		def default_dmx_meshdata_stream(dm, name, flags, data):
			return dmx_meshdata_stream(dm, name + ":0", name, name, flags, data)

		def dmx_meshdata_stream_array(streams):
			size = len(streams[0]["data"])
			if not all(len(stream["data"]) == size for stream in streams[1:]):
				raise ValueError("Inconsistent mesh data stream size")

			array = dm.add_element(None, "CDmePolygonMeshDataArray")
			array["size"] = size
			array["streams"] = dmx_array(streams)

			return array

		pos_stream = default_dmx_meshdata_stream(dm, "position", 3, mesh.positions())
		data["vertexData"] = dmx_meshdata_stream_array([pos_stream])

		uv_stream = default_dmx_meshdata_stream(dm, "texcoord", 1, mesh.uvs())
		normal_stream = default_dmx_meshdata_stream(dm, "normal", 1, mesh.normals())
		tangent_stream = default_dmx_meshdata_stream(dm, "tangent", 1, mesh.tangents())
		data["faceVertexData"] = dmx_meshdata_stream_array([uv_stream, normal_stream, tangent_stream])

		edge_flags_stream = default_dmx_meshdata_stream(dm, "flags", 1, mesh.edge_flags())
		data["edgeData"] = dmx_meshdata_stream_array([edge_flags_stream])

		tex_scale_stream = default_dmx_meshdata_stream(dm, "textureScale", 0, mesh.tex_scales())
		tex_axesU_stream = default_dmx_meshdata_stream(dm, "textureAxisU", 0, mesh.tex_axesU())
		tex_axesV_stream = default_dmx_meshdata_stream(dm, "textureAxisV", 0, mesh.tex_axesV())
		tex_mat_index_stream = default_dmx_meshdata_stream(dm, "materialindex", 8, mesh.material_indices())
		face_flags_stream = default_dmx_meshdata_stream(dm, "flags", 3, mesh.face_flags())
		lm_scale_bias_stream = default_dmx_meshdata_stream(dm, "lightmapScaleBias", 1, mesh.lm_scale_biases())
		data["faceData"] = dmx_meshdata_stream_array([tex_scale_stream, tex_axesU_stream,
			tex_axesV_stream, tex_mat_index_stream, face_flags_stream, lm_scale_bias_stream])

		subdivision_data = dm.add_element(None, "CDmePolygonMeshSubdivisionData")
		subdivision_data["subdivisionLevels"] = dmx_array([0 for i in range(len(uv_stream["data"]))]) # HACK
		subdivision_data["streams"] = dmx.make_array(None, dmx.Element)
		data["subdivisionData"] = subdivision_data

		return data

	@staticmethod
	def regenerate(vmap_desc, t3d_desc, obj_desc):
		dm = dmx.load("template_map.vmap")

		#globalClasses = []
		#hp_ents.buildEntities(t3d_desc.path(), globalClasses, 0)
		#for ent in globalClasses:
		#	dm.root["world"]["children"].append(ent.toEntityElement(dm))

		e = dm.add_element(None, "CMapMesh")

		# TODO: un-hardcode this
		e["origin"] = dmx.Vector3([0, 0, 0])
		e["angles"] = dmx.QAngle([0, 0, 0])
		e["scales"] = dmx.Vector3([0, 0, 0])
		if len(dm.root["world"]["children"]) > 0:
			node_id = int(dm.root["world"]["children"][-1]["nodeID"]) + 1
		else:
			node_id = 2
		e["nodeID"] = node_id
		e["referenceID"] = dmx.uint64(str(node_id))
		e["children"] = dmx.make_array(None, dmx.Element)
		e["editorOnly"] = False
		e["force_hidden"] = False
		e["transformLocked"] = False
		e["variableTargetKeys"] = dmx.make_array(None, str)
		e["variableNames"] = dmx.make_array(None, str)
		e["cubeMapName"] = ""
		e["lightGroup"] = ""
		e["visexclude"] = False
		e["renderwithdynamic"] = False
		e["disableHeightDisplacement"] = False
		e["fademindist"] = -1.
		e["fademaxdist"] = 0.
		e["bakelighting"] = True
		e["precomputelightprobes"] = True
		e["renderToCubemaps"] = True
		e["disableShadows"] = False
		e["smoothingAngle"] = 40.
		#e["tintColor"] = dmx.Color([255, 255, 255, 255])
		e["physicsType"] = "default"
		e["physicsGroup"] = ""
		e["physicsInteractsAs"] = ""
		e["physicsInteractsWith"] = ""
		e["physicsInteractsExclude"] = ""

		mesh = halfedge_mesh.Mesh.from_t3d(t3d_desc)
		e["meshData"] = VmapType.get_mesh_data(dm, mesh)

		e["physicsSimplificationOverride"] = False
		e["physicsSimplificationError"] = 0.

		dm.root["world"]["children"].append(e)

		dm.write(vmap_desc.path(), "keyvalues2", 4)