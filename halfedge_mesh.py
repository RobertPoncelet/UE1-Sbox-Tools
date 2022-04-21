from csg.core import CSG
from csg.geom import Polygon, Vector, Vertex

def from_obj(obj_desc):
    vertices = []
    uvs = []
    faces = []
    with open(obj_desc.path()) as obj:
        for line in obj.readlines():
            parts = line.split()
            if parts[0] == "v":
                pos = [float(i) for i in parts[1:4]]
                vertices.append(Vertex(Vector(pos)))
            elif parts[0] == "vt":
                uv = [float(i) for i in parts[1:3]]
                uvs.append(uv)
            elif parts[0] == "f":
                indices = [p.split("/")[0] for p in parts[1:]]
                face = Polygon([vertices[i] for i in indices])
                faces.append(face)
    return HalfEdgeMesh(faces)

class HalfEdgeMesh:
    def __init__(polygons):
        pass

    
