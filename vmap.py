import t3d_to_entities

class T3dType:
    force_regen = False
    file_extension = "t3d"
    category = "map"

class VmapType:
    force_regen = False
    file_extension = "vmap"
    category = "map"

    @staticmethod
    def resolve_dependencies(vmap_desc, t3d_desc):
        vmap_desc.add_dependency_on(t3d_desc)

    @staticmethod
    def regenerate(vmap_desc, t3d_desc):
        t3d_to_entities.convertMapFileToDMX(t3d_desc.path(), vmap_desc.path())