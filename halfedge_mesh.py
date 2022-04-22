from csg.core import CSG
from csg.geom import Polygon, Vector, Vertex

def from_obj(obj_desc):
    vertices = []
    uvs = []
    faces = []
    with open(obj_desc.path()) as obj:
        for line in obj.readlines():
            try:
                parts = line.split()
                if parts[0] == "v":
                    pos = [float(i) for i in parts[1:4]]
                    vertices.append(Vertex(Vector(pos)))
                elif parts[0] == "vt":
                    uv = [float(i) for i in parts[1:3]]
                    uvs.append(uv)
                elif parts[0] == "f":
                    indices = [int(p.split("/")[0]) for p in parts[1:]]
                    # TODO: use HalfEdgeVertex to add UVs
                    face = Polygon([vertices[i-1] for i in indices])
                    faces.append(face)
            except ZeroDivisionError:
                print("Bad face:", [vertices[i-1] for i in indices])

    return HalfEdgeMesh(faces)

def TEMP_const_int_array(l):
        return [int(i) for i in l]

def TEMP_const_vec_array(l):
    return [[float(i) for i in s.split()] for s in l]

class HalfEdgeMesh:
    class HalfEdge:
        def __init__(self, vertex, face, next_edge, opp_edge):
            self.vertex = vertex
            self.face = face
            self.next_edge = next_edge
            self.opp_edge = opp_edge

    class HalfEdgeVertex(Vertex):
        def __init__(self, pos, halfedge, uv, normal=None):
            super().__init__(pos, normal)
            self.halfedge = halfedge
            self.uv = uv

        def interpolate(self, other, t):
            def lerp(a, b):
                return t*b + (1-t)*a

            ret = super().interpolate(other, t)
            ret.uv[0] = lerp(self.uv[0], other.uv[0])
            ret.uv[1] = lerp(self.uv[1], other.uv[1])

        def clone(self):
            ret = super().clone()
            ret.uv = list(self.uv)
            return ret

    def __init__(self, polygons: list[Polygon]):
        self._faces = polygons
        self._vertices = []
        self._halfedges = {}

        # Make a list of ALL the vertices
        # This could be done more concisely but whatever
        for f in self._faces:
            for v in f.vertices:
                if v not in self._vertices:
                    self._vertices.append(v)

        def edge_key(v1, v2):
            return self._vertices.index(v1), self._vertices.index(v2)

        def face_edges(face):
            for vi1, v1 in enumerate(face.vertices):
                vi2 = (vi1 + 1) % len(face.vertices)
                v2 = f.vertices[vi2]
                yield vi1, v1, vi2, v2

        # Create all the HalfEdges
        for f in self._faces:
            for _, v1, _, v2 in face_edges(f):
                key = edge_key(v1, v2)
                # Neighbour references are None for now, we'll update them later
                self._halfedges[key] = HalfEdgeMesh.HalfEdge(v2, f, None, None)

        # Link them up
        for f in self._faces: # TODO: SO pseudocode doesn't have it, but surely this line is needed, right?
            f.halfedge = self._halfedges[edge_key(f.vertices[0], f.vertices[1])]
            for _, v1, vi2, v2 in face_edges(f):
                this_key = edge_key(v1, v2)
                v1.halfedge = self._halfedges[this_key]
                vi3 = (vi2 + 1) % len(f.vertices)
                v3 = f.vertices[vi3]
                next_key = edge_key(v2, v3)
                self._halfedges[this_key].next_edge = self._halfedges[next_key]
                opp_key = edge_key(v2, v1)
                if opp_key in self._halfedges:
                    self._halfedges[this_key].opp_edge = self._halfedges[opp_key]
                    self._halfedges[opp_key].opp_edge = self._halfedges[this_key]

    # TODO: everything
    def vertex_edge_indices(self):
        return TEMP_const_int_array([
            "0",
            "1",
            "22",
            "15",
            "8",
            "14",
            "6",
            "18"
        ])
    def vertex_data_indices(self):
        return TEMP_const_int_array([
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7"
        ])
    def edge_vertex_indices(self):
        return TEMP_const_int_array([
            "1",
            "0",
            "5",
            "1",
            "2",
            "5",
            "1",
            "6",
            "3",
            "4",
            "6",
            "3",
            "7",
            "6",
            "3",
            "5",
            "7",
            "4",
            "0",
            "7",
            "2",
            "0",
            "4",
            "2"
        ])
    def edge_opposite_indices(self):
        return TEMP_const_int_array([
            "1",
            "0",
            "3",
            "2",
            "5",
            "4",
            "7",
            "6",
            "9",
            "8",
            "11",
            "10",
            "13",
            "12",
            "15",
            "14",
            "17",
            "16",
            "19",
            "18",
            "21",
            "20",
            "23",
            "22"
        ])
    def edge_next_indices(self):
        return TEMP_const_int_array([
            "2",
            "19",
            "4",
            "7",
            "21",
            "14",
            "1",
            "11",
            "10",
            "23",
            "12",
            "15",
            "17",
            "6",
            "9",
            "3",
            "18",
            "8",
            "20",
            "13",
            "22",
            "0",
            "16",
            "5"
        ])
    def edge_face_indices(self):
        return TEMP_const_int_array([
            "0",
            "5",
            "0",
            "3",
            "0",
            "4",
            "5",
            "3",
            "1",
            "4",
            "1",
            "3",
            "1",
            "5",
            "4",
            "3",
            "2",
            "1",
            "2",
            "5",
            "2",
            "0",
            "2",
            "4"
        ])
    def edge_data_indices(self):
        return TEMP_const_int_array([
            "0",
            "0",
            "1",
            "1",
            "2",
            "2",
            "3",
            "3",
            "4",
            "4",
            "5",
            "5",
            "6",
            "6",
            "7",
            "7",
            "8",
            "8",
            "9",
            "9",
            "10",
            "10",
            "11",
            "11"
        ])
    def edge_vertex_data_indices(self):
        return TEMP_const_int_array([
            "4",
            "1",
            "12",
            "2",
            "21",
            "3",
            "13",
            "20",
            "15",
            "5",
            "18",
            "6",
            "17",
            "7",
            "19",
            "16",
            "23",
            "9",
            "14",
            "10",
            "0",
            "11",
            "22",
            "8"
        ])
    def face_edge_indices(self):
        return TEMP_const_int_array([
            "21",
            "17",
            "22",
            "15",
            "14",
            "6"
        ])
    def face_data_indices(self):
        return TEMP_const_int_array([
            "0",
            "1",
            "2",
            "3",
            "4",
            "5"
        ])

    def materials(self):
        return ["hp1/materials/harrypotter/chocolatefrogtex0.vmat"]

    def positions(self):
        return TEMP_const_vec_array([
            "-32 -64 96",
            "32 -64 96",
            "-32 64 96",
            "32 64 -96",
            "-32 64 -96",
            "32 64 96",
            "32 -64 -96",
            "-32 -64 -96"
        ])

    def uvs(self):
        return TEMP_const_vec_array([
            "0 -6",
            "0 -6",
            "-4 -6",
            "2 -6",
            "2 4",
            "0 0",
            "0 0",
            "2 0",
            "0 -6",
            "0 0",
            "0 0",
            "0 4",
            "2 0",
            "2 -6",
            "-4 -6",
            "2 0",
            "0 -6",
            "0 4",
            "2 4",	
            "2 0",
            "-4 0",
            "0 0",
            "0 0",
            "-4 0"
        ])
    def normals(self):
        return TEMP_const_vec_array([
            "-1 0 0",
            "0 -1 0",
            "1 0 0",
            "0 1 0",
            "0 0 1",
            "0 1 0",
            "1 0 0",
            "0 -1 0",
            "0 1 0",
            "0 0 -1",
            "0 -1 0",
            "0 0 1",
            "0 0 1",
            "0 -1 0",
            "-1 0 0",
            "0 0 -1",
            "1 0 0",
            "0 0 -1",
            "0 0 -1",
            "0 1 0",
            "1 0 0",
            "0 0 1",
            "-1 0 0",
            "-1 0 0"
        ])
    def tangents(self):
        return TEMP_const_vec_array([
            "0 1 0 1",
            "1 0 0 -1",
            "0 1 0 -1",
            "1 -0 0 1",
            "1 0 0 -1",
            "1 -0 0 1",
            "0 1 0 -1",
            "1 0 0 -1",
            "1 -0 0 1",
            "1 0 0 1",
            "1 0 0 -1",
            "1 0 0 -1",
            "1 0 0 -1",
            "1 0 0 -1",
            "0 1 0 1",
            "1 0 0 1",
            "0 1 0 -1",
            "1 0 0 1",
            "1 0 0 1",
            "1 -0 0 1",
            "0 1 0 -1",
            "1 0 0 -1",
            "0 1 0 1",
            "0 1 0 1"
        ])
        
    def edge_flags(self):
        return TEMP_const_int_array([
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0"
        ])

    def tex_scales(self):
        return TEMP_const_vec_array([
            "0.25 0.25",
            "0.25 0.25",
            "0.25 0.25",
            "0.25 0.25",
            "0.25 0.25",
            "0.25 0.25"
        ])
    def tex_axesU(self):
        return TEMP_const_vec_array([
            "1 0 0 0",
            "1 0 0 0",
            "0 1 0 0",
            "0 1 0 0",
            "1 0 0 0",
            "1 0 0 0"
        ])
    def tex_axesV(self):
        return TEMP_const_vec_array([
            "0 -1 0 0",
            "0 -1 0 0",
            "0 0 -1 0",
            "0 0 -1 0",
            "0 0 -1 0",
            "0 0 -1 0"
        ])
    def material_indices(self):
        return TEMP_const_int_array([
            "0",
            "0",
            "0",
            "0",
            "0",
            "0"
        ])
    def face_flags(self):
        return TEMP_const_int_array([
            "0",
            "0",
            "0",
            "0",
            "0",
            "0"
        ])
    def lm_scale_biases(self):
        return TEMP_const_int_array([
            "0",
            "0",
            "0",
            "0",
            "0",
            "0"
        ])