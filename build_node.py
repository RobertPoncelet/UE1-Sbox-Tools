import os

class BuildNode(object):
    force_regen = False

    def __init__(self, filepath):
        self._filepath = filepath

    @property
    def filepath(self):
        return self._filepath

    @property
    def mtime(self):
        return os.path.getmtime(self.filepath)

    # Return the timestamp of our own asset path
    def build(self):
        file_exists = os.path.isfile(self.filepath)
        assert(file_exists or self.dependencies)
        if self.dependencies:
            dep_mtime = max(dep.build() for dep in self.dependencies)
            file_outdated = dep_mtime > self.mtime
        else:
            file_outdated = False
        if type(self).force_regen or not file_exists or file_outdated:
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