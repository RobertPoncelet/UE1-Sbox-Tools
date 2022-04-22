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

def normal(face):
    v1 = face.vertices[1].pos.minus(face.vertices[0].pos)
    v2 = face.vertices[2].pos.minus(face.vertices[0].pos)
    return v1.cross(v2).unit()

def tangent(face):
    v1 = face.vertices[1].pos.minus(face.vertices[0].pos)
    return v1.unit()

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
            ret.halfedge = self.halfedge
            return ret

    def __init__(self, polygons: "list[Polygon]"):
        self._faces = polygons
        self._vertices = []
        self._face_vertices = []
        self._halfedges = {}

        # Make a list of ALL the vertices
        # This could be done more concisely but nested list comprehension syntax make brain hurty
        for f in self._faces:
            for v in f.vertices:
                if v not in self._vertices:
                    self._vertices.append(v)
                self._face_vertices.append(v)

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
                # We need to make the opposing HalfEdge even if it has no face
                opp_key = edge_key(v2, v1)
                if opp_key not in self._halfedges:
                    self._halfedges[opp_key] = HalfEdgeMesh.HalfEdge(v1, None, None, None)

        # Link them up
        for f in self._faces: # TODO: SO pseudocode doesn't have it, but surely this line is needed, right?
            f.halfedge = self._halfedges[edge_key(f.vertices[0], f.vertices[1])]
            for vi1, v1, vi2, v2 in face_edges(f):
                this_key = edge_key(v1, v2)
                v1.halfedge = self._halfedges[this_key]
                vi3 = (vi2 + 1) % len(f.vertices)
                v3 = f.vertices[vi3]
                next_key = edge_key(v2, v3)
                self._halfedges[this_key].next_edge = self._halfedges[next_key]
                opp_key = edge_key(v2, v1)
                self._halfedges[this_key].opp_edge = self._halfedges[opp_key]
                self._halfedges[opp_key].opp_edge = self._halfedges[this_key]
                # If the opposing edge has no face, we need to set its "next" here
                if not self._halfedges[opp_key].face:
                    if self._halfedges[opp_key].next_edge:
                        print("My logic was wrong :(")
                    vi0 = (vi1 - 1) % len(f.vertices)
                    v0 = f.vertices[vi0]
                    opp_next_key = edge_key(v1, v0)
                    self._halfedges[opp_key].next_edge = self._halfedges[opp_next_key]
                    new_vert = v1.clone()
                    new_vert.halfedge = v1.halfedge # TODO: not needed when we're using our own Vertex subclass
                    new_vert.flip()
                    self._face_vertices.append(new_vert)


        # Turn the HalfEdge dict into a list so we can use indices
        self._halfedges = list(self._halfedges.values())

        #print(self._faces)
        #print(self._halfedges)
        #print(self._vertices)
        #print(self._face_vertices)

    def vertex_edge_indices(self):
        return [self._halfedges.index(v.halfedge) for v in self._vertices]

    def vertex_data_indices(self):
        return [i for i in range(len(self._vertices))]

    def edge_vertex_indices(self):
        return [self._vertices.index(e.vertex) for e in self._halfedges]

    def edge_opposite_indices(self):
        return [self._halfedges.index(e.opp_edge) for e in self._halfedges]

    def edge_next_indices(self):
        return [self._halfedges.index(e.next_edge) for e in self._halfedges]

    def edge_face_indices(self):
        return [(self._faces.index(e.face) if e.face else -1) for e in self._halfedges]

    def edge_data_indices(self):
        return [int(i/2) for i in range(len(self._halfedges))]

    def edge_vertex_data_indices(self):
        return [self._face_vertices.index(e.vertex) for e in self._halfedges]

    def face_edge_indices(self):
        return [self._halfedges.index(f.halfedge) for f in self._faces]

    def face_data_indices(self):
        return [i for i in range(len(self._faces))]

    def materials(self):
        return ["hp1/materials/harrypotter/chocolatefrogtex0.vmat"]

    def positions(self):
        return [tuple(v.pos) for v in self._vertices]

    def uvs(self):
        return [(0., 0.) for v in self._face_vertices] # TODO

    def normals(self):
        return [tuple(normal(v.halfedge.face)) for v in self._face_vertices]

    def tangents(self):
        return [list(tangent(v.halfedge.face)) + [1.] for v in self._face_vertices]
        
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