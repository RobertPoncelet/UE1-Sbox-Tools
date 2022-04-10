import os

import asset

class BuildNode(object):
    force_regen = False

    def __init__(self, asset_desc: asset.AssetDescription):
        self._asset = asset_desc

    @property
    def filepath(self):
        return self._asset.path()

    @property
    def relative_filepath(self):
        return self._asset.path(relative_to_root=True)

    @property
    def mtime(self):
        return os.path.getmtime(self.filepath)

    # Return the timestamp of our own asset path
    def build(self):
        file_exists = os.path.isfile(self.filepath)
        #assert(file_exists or self.dependencies)
        if file_exists and self.dependencies:
            dep_mtime = max(dep.build() for dep in self.dependencies)
            file_outdated = dep_mtime > self.mtime
        else:
            file_outdated = False
        if type(self).force_regen or not file_exists or file_outdated:
            print("Generating", type(self).__name__, self.filepath)
            directory = os.path.dirname(self.filepath)
            if not os.path.isdir(directory):
                print("Making directory", directory)
                os.makedirs(directory)
            self.regenerate_file()
        assert(os.path.isfile(self.filepath))
        return self.mtime

    # Return a list of BuildNodes
    @property
    def dependencies(self):
        raise NotImplementedError("Please use a subclass of BuildNode.")

    # Convert dependencies to a file in the filepath
    def regenerate_file(self):
        raise NotImplementedError("Please use a subclass of BuildNode.")

# Use this class for original source files which have no dependencies
class SourceFileNode(BuildNode):
    @property
    def dependencies(self):
        return None