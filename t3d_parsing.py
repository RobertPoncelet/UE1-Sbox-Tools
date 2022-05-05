import constants

class Actor:
    def __init__(self, line):
        if not line.startswith("Begin Actor"):
            print(line)
            raise SyntaxError("This doesn't look like an Actor begin line - parse error?")
        self.keyvalues = {}
        self.brush = None
        words = line.split()[2:]
        for key, value in [word.split("=") for word in words]:
            self.keyvalues[key] = value

    def parseLine(self, line):
        key = line[:line.find("=")].strip()
        value = line[line.find("=")+1:].strip()
        self.keyvalues[key] = value

    def addChild(self, child):
        if self.brush:
            raise SyntaxError("More than 1 Brush in this Actor!")
        self.brush = child

    def __repr__(self):
        return "Actor({}, {})".format(self.keyvalues, self.brush)

class Brush:
    def __init__(self, line):
        self.name = line.split("=")[-1]
        self.polygons = []

    def parseLine(self, line):
        pass

    def addChild(self, child):
        self.polygons.append(child)

    def __repr__(self):
        return "Brush({})".format(self.polygons)

class Polygon:
    def __init__(self, line):
        words = line.split()[2:]
        keyvalues = dict(word.split("=") for word in words)
        self.item = keyvalues.get("Item")
        self.texture = keyvalues.get("Texture")
        self.flags = int(keyvalues.get("Flags", 0))
        self.link = int(keyvalues.get("Link", 0))
        self.vertices = []

    def parseLine(self, line):
        words = line.split()
        key = words[0]
        if key == "Pan":
            self.pan = [int(s.split("=")[-1]) for s in words[1:]]
        elif key in ["Origin", "Normal", "TextureU", "TextureV", "Vertex"]:
            value = tuple(float(s) for s in words[1].split(","))
            if key == "Vertex":
                self.vertices.append(value)
            else:
                setattr(self, key.lower(), value)
        else:
            raise SyntaxError("Unexpected Polygon keyvalue {}={}!".format(key, words[1:]))

    def addChild(self, child):
        raise SyntaxError("Polygons shouldn't have any child objects!")

    def __repr__(self):
        return "Polygon with {} vertices".format(len(self.vertices))

def getActors(path):
    stack = []
    actors = []

    parseDict = {
        "Actor": Actor,
        "Brush": Brush,
        "Polygon": Polygon
    }
    
    with open(path) as file:
        for line in file:
            words = line.split()
            if words and words[0] == "Begin":
                currentItem = words[1]
                if currentItem in parseDict:
                    currentObject = parseDict[currentItem](line)
                    stack.append(currentObject)

            elif words and words[0] == "End":
                currentItem = words[1]
                if currentItem in parseDict:
                    done = stack.pop()
                    if stack:
                        stack[-1].addChild(done)
                    else:
                        actors.append(done)

            elif stack:
                stack[-1].parseLine(line)

    return actors

def transformKeyValues(kvString):
    try:
        kvString = kvString[1:-1] # Remove brackets
        values = kvString.split(",")
        values = {v.split("=")[0] : float(v.split("=")[1]) for v in values}
    except IndexError:
        values = {}
    return values

def locationToOrigin(location):
    dims = transformKeyValues(location)
    pos = [0., 0., 0.]
    for d in dims:
        if d == "X":
            pos[0] = dims[d]
        elif d == "Y":
            pos[1] = dims[d]
        elif d == "Z":
            pos[2] = dims[d]
    return "{} {} {}".format(pos[0]*constants.SCALE, -pos[1]*constants.SCALE, pos[2]*constants.SCALE) # Y is flipped

def rotationToAngles(rotation, yawOffset=0.):
    values = transformKeyValues(rotation)
    angles = [0., 0., 0.]
    factor = -360. / 65536. # Unreal rotations seem to be encoded as 16-bit ints
    for key in values:
        if key == "Pitch":
            angles[0] = values[key] * factor * -1. - 180.
        elif key == "Yaw":
            angles[1] = values[key] * factor - 180. + yawOffset
        elif key == "Roll":
            angles[2] = values[key] * factor - 180.
    # Hammer stores rotations as Y Z X
    return "{} {} {}".format(angles[2], angles[1], angles[0])