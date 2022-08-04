import os, subprocess

import datamodel as dmx
import asset, constants, halfedge_mesh, hp_ents, t3d_parsing
from csg.core import CSG

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
		#obj_desc = t3d_desc.clone()
		#obj_desc.stage = "intermediate"
		#obj_desc.asset_type = ObjType
		#obj_desc.resolve_dependencies(t3d_desc)
		#vmap_desc.add_dependency_on(obj_desc)
		actors = t3d_parsing.getActors(t3d_desc.path())
		setattr(t3d_desc, "actors", actors)

	@staticmethod
	def regenerate(vmap_desc, t3d_desc):
		dm = dmx.load("template_map.vmap")

		# Stick all the world brushes together into one
		brush_actors = [a for a in t3d_desc.actors if a["Class"] == "Brush"]
		world_brush = CSG.fromPolygons([])
		num_actors = len(brush_actors)
		num_done = 0
		for b in brush_actors:
			if "CsgOper" not in b.keyvalues:
				continue
			if b["CsgOper"] == "CSG_Add":
				new_brush = halfedge_mesh.t3d_brush_to_csg(b.brush)
				world_brush = world_brush.union(new_brush)
				num_done += 1
				progress = int(round((float(num_done)/float(num_actors)) * 100))
				print("Progress: {}%".format(progress))
		for b in brush_actors:
			if "CsgOper" not in b.keyvalues:
				continue
			if b["CsgOper"] == "CSG_Subtract":
				new_brush = halfedge_mesh.t3d_brush_to_csg(b.brush)
				world_brush = world_brush.subtract(new_brush)
				num_done += 1
				progress = int(round((float(num_done)/float(num_actors)) * 100))
				print("Progress: {}%".format(progress))

		# Remove the world brushes from the actor list and replace them with our new one
		t3d_desc.actors = [a for a in t3d_desc.actors if a["Class"] != "Brush"]
		world = {"Class": "Brush", "Name": "World", "Location": "(X=0,Y=0,Z=0)"}
		setattr(world, "brush", world_brush)
		t3d_desc.actors.append(world)

		entities = []

		hp_ents.buildEntities(t3d_desc.actors, entities, 0, t3d_desc.name)
		for ent in entities:
			dm.root["world"]["children"].append(ent.toDmxElement(dm))

		dm.write(vmap_desc.path(), "keyvalues2", 4)