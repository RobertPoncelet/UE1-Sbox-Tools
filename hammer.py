from dataclasses import dataclass
import datamodel as dmx

@dataclass
class EntityIO:
	outputName: str
	targetName: str
	inputName: str
	overrideParam: str
	delay: float = 0.0
	timesToFire: int = -1
	targetType: int = 7 # TODO: is it ever anything else?

class HammerClass:    
	def __init__(self, inName):
		self.className = inName
		self.properties = {}
		self.classes = []
		self.dmxConnections = []
		self.brush = None
		self.f = None
		self.indentLevel = 0
		
	def writeLine(self, string):
		for i in range(0, self.indentLevel):
			self.f.write("\t")
		self.f.write(string + "\n")
		
	def addProperty(self, name, value):
		self.properties[name] = value
		
	def addClass(self, hClass):
		self.classes.append(hClass)

	def getTemplateElement(self, datamodel):
		if self.properties["classname"]:
			classType = "CMapEntity"
		else:
			classType = "CMapMesh"
		e = datamodel.add_element(None, classType)
		e["children"] = dmx.make_array(None, dmx.Element)
		e["editorOnly"] = False
		e["force_hidden"] = False
		e["transformLocked"] = False
		e["variableTargetKeys"] = dmx.make_array(None, str)
		e["variableNames"] = dmx.make_array(None, str)
		relayPlugData = datamodel.add_element(None, "DmePlugList")
		relayPlugData["names"] = dmx.make_array(None, str)
		relayPlugData["dataTypes"] = dmx.make_array(None, int)
		relayPlugData["plugTypes"] = dmx.make_array(None, int)
		relayPlugData["descriptions"] = dmx.make_array(None, str)
		e["relayPlugData"] = relayPlugData
		e["connectionsData"] = dmx.make_array(None, dmx.Element)
		e["entity_properties"] = datamodel.add_element(None, "EditGameClassProps")
		e["hitNormal"] = dmx.Vector3([0, 0, 1])
		e["isProceduralEntity"] = False

		return e

	def createDmxConnection(self, connection, datamodel):
		c = datamodel.add_element(None, "DmeConnectionData")
		c["outputName"] = str(connection.outputName)
		c["targetName"] = str(connection.targetName)
		c["inputName"] = str(connection.inputName)
		c["overrideParam"] = str(connection.overrideParam) if connection.overrideParam else ""
		c["delay"] = float(connection.delay)
		c["timesToFire"] = int(connection.timesToFire)
		c["targetType"] = int(connection.targetType)
		return c

	def getMeshData(self, dm, mesh):
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

	def makeMesh(self, e, dm):
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

		e["meshData"] = self.getMeshData(dm, self.brush)

		e["physicsSimplificationOverride"] = False
		e["physicsSimplificationError"] = 0.

		return e

	def toDmxElement(self, datamodel):
		e = self.getTemplateElement(datamodel)

		props = dict(self.properties) # Make a copy so we can remove stuff

		if "origin" in props:
			e["origin"] = dmx.Vector3(props["origin"].split())
			del(props["origin"])
		if "angles" in props:
			e["angles"] = dmx.QAngle(props["angles"].split())
			del(props["angles"])
		if "scales" in props:
			e["scales"] = dmx.Vector3(props["scales"].split())
			del(props["scales"])
		if "id" in props:
			e["nodeID"] = int(props["id"])
			e["referenceID"] = dmx.uint64(props["id"])
			del(props["id"])

		# TODO: other default keyvalues

		for key in props:
			e["entity_properties"][key] = str(props[key])
		
		for c in self.dmxConnections:
			e["connectionsData"].append(self.createDmxConnection(c, datamodel))

		if self.brush:
			if not self.properties["classname"]:
				self.makeMesh(e, datamodel)
			else:
				brushElement = datamodel.add_element(None, "CMapMesh")
				self.makeMesh(brushElement, datamodel)
				e["children"] = dmx.make_array(None, dmx.Element)
				e["children"].append(brushElement)

		return e
		
	def addOutput(self, outputName, target, targetInput, param, delay, maxTimes):
		if not any(c.className == "connections" for c in self.classes):
			self.addClass(HammerClass("connections"))
		for c in self.classes:
			if c.className == "connections":
				args = ["" if s is None else s for s in [target, targetInput, param, delay, maxTimes]]
				value = ",".join([str(s) for s in args])
				c.addProperty(outputName, value)
				break
		self.dmxConnections.append(EntityIO(outputName, target, targetInput, param, delay, maxTimes))
		
	def write(self, inFile, inIndentLevel):
		self.f = inFile
		self.indentLevel = inIndentLevel
		self.writeLine(self.className)
		self.writeLine("{")
		self.indentLevel += 1
		for p in self.properties:
			pString = "\"{0}\" \"{1}\"".format(p, self.properties[p])
			self.writeLine(pString)
		for c in self.classes:
			c.write(self.f, self.indentLevel)
		self.indentLevel -= 1
		self.writeLine("}")