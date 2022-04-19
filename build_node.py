import os

import asset

class BuildNode:
    def __init__(self, asset_desc: asset.AssetDescription):
        if type(asset_desc) is not asset.AssetDescription:
            raise asset.InvalidAssetError("BuildNode() only takes AssetDescriptions.")
        self._asset = asset_desc
        self._dependency_nodes = None

    @property
    def filepath(self):
        return self._asset.path()

    @property
    def mtime(self):
        return os.path.getmtime(self.filepath)

    # Return the timestamp of our own asset path
    def build(self):
        file_exists = os.path.isfile(self.filepath)
        assert(file_exists or self.dependencies())
        if self.dependencies():
            dep_mtime = max(dep.build() for dep in self.dependencies())
            file_outdated = not file_exists or dep_mtime > self.mtime
        else:
            file_outdated = False
        if self._asset.asset_type.force_regen or not file_exists or file_outdated:
            print("Generating", self._asset.asset_type.__name__, self.filepath)
            directory = os.path.dirname(self.filepath)
            if not os.path.isdir(directory):
                print("Making directory", directory)
                os.makedirs(directory)
            self._asset.regenerate()
        assert(os.path.isfile(self.filepath))
        return self.mtime

    # Return a list of BuildNodes
    def dependencies(self):
        if not self._dependency_nodes:
            self._dependency_nodes = [BuildNode(i) for i in self._asset.dependencies]
        return self._dependency_nodes