from build_node import BuildNode, SourceFileNode
from PIL import Image

class ColorPngNode(BuildNode):
    def __init__(self, desc, tga):
        super().__init__(desc)
        self._dependencies = [SourceFileNode(tga)]

    @property
    def dependencies(self):
        return self._dependencies
    
    def regenerate_file(self):
        im = Image.open(self.dependencies[0].filepath)
        im.save(self.filepath)

class VmatNode(BuildNode):
    def __init__(self, desc, tree):
        super().__init__(desc)
        index = tree.vmats.index(desc)
        tga = tree.tgas[index]
        png = desc.clone()
        png.stage = "converted"
        png.filetype = "png"

        self._dependencies = [ColorPngNode(png, tga)]

    @property
    def dependencies(self):
        return self._dependencies

    def regenerate_file(self):
        with open("template.vmat") as template, open(self.filepath, "w") as matfile:
            text = template.read()
            mat_dict = {
                "tex_color": self.dependencies[0].sbox_filepath,
                "tex_trans": "materials/default/default_trans.tga",
                "alpha_test": "0",
                "shader": "complex.vfx"
            }
            text = text.format(**mat_dict)
            matfile.write(text)