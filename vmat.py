from PIL import Image

class PngType:
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
        if png_desc.save_alpha:
            if len(im.split()) < 4:
                print(tga_desc.path(), "has fewer than 4 image channels")
            else:
                im = im.split()[3]
        im.save(png_desc.path())

class VmatType:
    force_regen = False
    file_extension = "vmat"
    category = "material"

    @staticmethod
    def resolve_dependencies(vmat_desc, tga_desc):
        png_desc = vmat_desc.clone()
        png_desc.asset_type = PngType
        png_desc.save_alpha = False
        png_desc.resolve_dependencies(tga_desc)
        vmat_desc.add_dependency_on("png_desc", png_desc)

        if vmat_desc.is_masked:
            t_png_desc = png_desc.clone()
            t_png_desc.save_alpha = True
            t_png_desc.name += "_trans"
            t_png_desc.resolve_dependencies(tga_desc)
            vmat_desc.add_dependency_on("t_png_desc", t_png_desc)

    @staticmethod
    def regenerate(vmat_desc, png_desc, t_png_desc=None):
        with open("template.vmat") as template, open(vmat_desc.path(), "w") as matfile:
            text = template.read()
            trans_path = t_png_desc.sbox_path() if t_png_desc \
                else "materials/default/default_trans.tga"
            mat_dict = {
                "tex_color": png_desc.sbox_path(),
                "tex_trans": trans_path,
                "alpha_test": int(vmat_desc.is_masked),
                "shader": "complex.vfx"
            }
            text = text.format(**mat_dict)
            matfile.write(text)