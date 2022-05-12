import os, subprocess

import datamodel as dmx
import asset, constants, halfedge_mesh, hp_ents, t3d_parsing

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
	def regenerate(vmap_desc, t3d_desc, obj_desc):
		dm = dmx.load("template_map.vmap")

		globalClasses = []
		actors = t3d_parsing.getActors(t3d_desc.path())
		mapname = t3d_desc.name
		hp_ents.buildEntities(actors, globalClasses, 0, t3d_desc.name)
		for ent in globalClasses:
			dm.root["world"]["children"].append(ent.toDmxElement(dm))

		dm.write(vmap_desc.path(), "keyvalues2", 4)