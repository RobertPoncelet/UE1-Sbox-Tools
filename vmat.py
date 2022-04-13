from PIL import Image

class ColorPngType:
    force_regen = False
    file_extension = "png"
    category = "material"

    @staticmethod
    def resolve_dependencies(png_desc, tga_desc):
        # TGA should have no dependencies
        png_desc.add_dependency_on("tga_desc", tga_desc)

    @staticmethod
    def regenerate(png_desc, tga_desc):
        im = Image.open(tga_desc.path())
        im.save(png_desc.path())

class VmatType:
    force_regen = False
    file_extension = "vmat"
    category = "material"

    @staticmethod
    def resolve_dependencies(vmat_desc, tga_desc):
        png_desc = vmat_desc.clone()
        png_desc.asset_type = ColorPngType
        png_desc.resolve_dependencies(tga_desc)

        vmat_desc.add_dependency_on("png_desc", png_desc)

    @staticmethod
    def regenerate(vmat_desc, png_desc):
        with open("template.vmat") as template, open(vmat_desc.path(), "w") as matfile:
            text = template.read()
            mat_dict = {
                "tex_color": png_desc.sbox_path(),
                "tex_trans": "materials/default/default_trans.tga",
                "alpha_test": "0",
                "shader": "complex.vfx"
            }
            text = text.format(**mat_dict)
            matfile.write(text)