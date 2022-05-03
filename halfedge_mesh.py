from csg.core import CSG
from csg.geom import Polygon, Vector, Vertex

def normal(face):
    v1 = face.vertices[1].pos.minus(face.vertices[0].pos)
    v2 = face.vertices[2].pos.minus(face.vertices[0].pos)
    return v1.cross(v2).unit()

def tangent(face):
    v1 = face.vertices[1].pos.minus(face.vertices[0].pos)
    return v1.unit()

class Mesh:
    @staticmethod
    def from_obj(obj_desc):
        vertices = []
        uvs = []
        faces = []
        with open(obj_desc.path()) as obj:
            for line in obj.readlines():
                parts = line.split()
                if not parts:
                    continue
                if parts[0] == "v":
                    pos = [float(i) for i in parts[1:4]]
                    vertices.append(Vertex(Vector(pos)))
                elif parts[0] == "vt":
                    uv = [float(i) for i in parts[1:3]]
                    uvs.append(uv)
                elif parts[0] == "f":
                    indices = [int(p.split("/")[0]) for p in parts[1:]]
                    # TODO: use HalfEdgeVertex to add UVs
                    vert_list = list(reversed([vertices[i-1] for i in indices]))
                    face = None
                    # Find an arrangement of the vertices so the first three aren't collinear
                    for _ in range(len(vert_list)):
                        try:
                            face = Polygon(vert_list)
                            break
                        except ZeroDivisionError:
                            v = vert_list.pop(-1)
                            vert_list.insert(0, v)
                    if not face:
                        raise ValueError("Bad face:", line, [vertices[i-1] for i in indices])
                    faces.append(face)

        return Mesh(faces)

    class HalfEdge:
        def __init__(self, vertex, face, face_vertex, next_edge, opp_edge):
            self.vertex = vertex
            self.face = face
            self.face_vertex = face_vertex
            self.next_edge = next_edge
            self.opp_edge = opp_edge

    class HalfEdgeVertex(Vertex):
        def __init__(self, pos, halfedge, uv, normal=None):
            super().__init__(pos, normal)
            self.halfedge = halfedge
            self.uv = uv
            self.is_dummy = False

        def interpolate(self, other, t):
            def lerp(a, b):
                return t*b + (1-t)*a

            ret = super().interpolate(other, t)
            ret.uv[0] = lerp(self.uv[0], other.uv[0])
            ret.uv[1] = lerp(self.uv[1], other.uv[1])

        def clone(self):
            ret = super().clone()
            ret.uv = list(self.uv)
            ret.halfedge = self.halfedge
            return ret

    def __init__(self, polygons: "list[Polygon]"):
        self._faces = polygons
        self._vertices = []
        self._face_vertices = []
        self._halfedges = {}

        # Create all the vertices
        for f in self._faces:
            f.face_vertices = []
            for v in f.vertices:
                if v not in self._vertices:
                    self._vertices.append(v)
                fv = v.clone()
                fv.is_dummy = False
                fv.face = f
                self._face_vertices.append(fv)
                f.face_vertices.append(fv)

        # Add their index within the vertex list, for optimisation purposes
        for i, v in enumerate(self._vertices):
            v.index = i

        def edge_key(v1, v2):
            return v1.index, v2.index

        def face_edges(face):
            for vi1, v1 in enumerate(face.vertices):
                vi2 = (vi1 + 1) % len(face.vertices)
                v2 = f.vertices[vi2]
                yield vi1, v1, vi2, v2

        # Create all the HalfEdges
        for f in self._faces:
            for _, v1, vi2, v2 in face_edges(f):
                key = edge_key(v1, v2)
                # Neighbour references are None for now, we'll update them later
                self._halfedges[key] = HalfEdgeMesh.HalfEdge(v2, f, f.face_vertices[vi2], None, None)
                opp_key = edge_key(v2, v1)
                if opp_key not in self._halfedges:
                    self._halfedges[opp_key] = HalfEdgeMesh.HalfEdge(v1, None, None, None, None)

        for f in self._faces:
            for _, v1, _, v2 in face_edges(f):
            # We need to make the opposing HalfEdge even if it has no face
                opp_key = edge_key(v2, v1)
                if not self._halfedges[opp_key].face_vertex:
                    dummy_vert = v1.clone()
                    #dummy_vert.halfedge = v1.halfedge # TODO: not needed when we're using our own Vertex subclass
                    dummy_vert.is_dummy = True
                    dummy_vert.face = None
                    dummy_vert.flip()
                    self._face_vertices.append(dummy_vert)
                    self._halfedges[opp_key].face_vertex = dummy_vert

        # Link them up
        for f in self._faces: # TODO: SO pseudocode doesn't have it, but surely this line is needed, right?
            f.halfedge = self._halfedges[edge_key(f.vertices[0], f.vertices[1])]
            for vi1, v1, vi2, v2 in face_edges(f):
                vi3 = (vi2 + 1) % len(f.vertices)
                v3 = f.vertices[vi3]
                this_key = edge_key(v1, v2)
                next_key = edge_key(v2, v3)
                v1.halfedge = self._halfedges[this_key]
                self._halfedges[this_key].next_edge = self._halfedges[next_key]
                opp_key = edge_key(v2, v1)
                v2.halfedge = self._halfedges[opp_key]
                self._halfedges[this_key].opp_edge = self._halfedges[opp_key]
                self._halfedges[opp_key].opp_edge = self._halfedges[this_key]
                # If the opposing edge has no face, we need to set its "next" here
                if not self._halfedges[opp_key].face:
                    if self._halfedges[opp_key].next_edge:
                        raise ValueError("Unexpected next edge on half-edge {}!".format(opp_key))
                    vi0 = (vi1 - 1) % len(f.vertices)
                    v0 = f.vertices[vi0]
                    opp_next_key = edge_key(v1, v0)
                    # Since this half-edge has no face, the next one must also have no face
                    if not self._halfedges[opp_next_key].face:
                        self._halfedges[opp_key].next_edge = self._halfedges[opp_next_key]
                    else:
                        # Time to brute-force it
                        for v in self._vertices:
                            opp_next_key = edge_key(v1, v)
                            if opp_next_key not in self._halfedges or v is v1 or v is v2:
                                continue
                            if not self._halfedges[opp_next_key].face:
                                self._halfedges[opp_key].next_edge = self._halfedges[opp_next_key]
                                break
                        if not self._halfedges[opp_key].next_edge:
                            raise ValueError("Couldn't find next edge from half-edge {}!".format(opp_key))

        # Turn the HalfEdge dict into a list so we can use indices
        self._halfedges = list(self._halfedges.values())

        # Add all the indices for optimisation purposes
        for i, f in enumerate(self._faces):
            f.index = i
        for i, fv in enumerate(self._face_vertices):
            fv.index = i
        for i, e in enumerate(self._halfedges):
            e.index = i

        #print(self._faces)
        #print(self._halfedges)
        #print(self._vertices)
        #print(self._face_vertices)

    def vertex_edge_indices(self):
        return [v.halfedge.index for v in self._vertices]

    def vertex_data_indices(self):
        return [i for i in range(len(self._vertices))]

    def edge_vertex_indices(self):
        return [e.vertex.index for e in self._halfedges]

    def edge_opposite_indices(self):
        return [e.opp_edge.index for e in self._halfedges]

    def edge_next_indices(self):
        return [e.next_edge.index for e in self._halfedges]

    def edge_face_indices(self):
        return [(e.face.index if e.face else -1) for e in self._halfedges]

    def edge_data_indices(self):
        return [int(i/2) for i in range(len(self._halfedges))]

    def edge_vertex_data_indices(self):
        return [e.face_vertex.index for e in self._halfedges]

    def face_edge_indices(self):
        return [f.halfedge.index for f in self._faces]

    def face_data_indices(self):
        return [i for i in range(len(self._faces))]

    def materials(self):
        return ["hp1/materials/harrypotter/chocolatefrogtex0.vmat"]

    def positions(self):
        return [tuple(v.pos) for v in self._vertices]

    def uvs(self):
        return [(0., 0.) for v in self._face_vertices] # TODO

    def normals(self):
        return [(list(normal(fv.face)) if not fv.is_dummy else [0., 0., 0.]) for fv in self._face_vertices]

    def tangents(self):
        return [(list(tangent(fv.face)) + [1.] if not fv.is_dummy else [0., 0., 0., 0.,]) for fv in self._face_vertices]
        
    def edge_flags(self):
        return [0 for i in range(len(self._halfedges)//2)]

    def tex_scales(self):
        return [(0.25, 0.25) for f in self._faces] # TODO

    def tex_axesU(self):
        return [list(tangent(f)) + [0.] for f in self._faces]

    def tex_axesV(self):
        return [list(tangent(f).cross(normal(f))) + [0.] for f in self._faces]

    def material_indices(self):
        return [0 for f in self._faces] # TODO

    def face_flags(self):
        return [0 for f in self._faces]

    def lm_scale_biases(self):
        return [0 for f in self._faces]

if __name__ == "__main__":
    import os, glob, subprocess, constants, asset
    objs = glob.glob("F:\Google Drive\hp_resources\intermediate_assets\hp1\maps\movers\Lev4_Sneak2.Mover55.obj")
    #objs = glob.glob("triplane.obj")
    for i, obj in enumerate(sorted(objs, key=lambda f: os.path.getsize(f))):
        script_path = os.path.realpath("blender_clean_obj.py")
        subprocess.run([constants.BLENDER_PATH,	"-b", "--python", script_path, "--", obj], capture_output=True)
        print(str(int((i/len(objs)) * 100.)) + "%", obj)
        mesh = Mesh.from_obj(asset.AssetDescription.from_path(obj))