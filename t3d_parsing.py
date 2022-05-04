import constants

class Actor:
    def __init__(self, line):
        assert(line.startswith("Begin Actor"))
        self.keyvalues = {}
        self.brush = None
        words = line.split()[2:]
        for word in words:
            keyvalue = word.split("=")
            if (len(keyvalue) != 2):
                print(line)
                raise SyntaxError("T3D file shouldn't look like this")
            self.keyvalues[keyvalue[0]] = keyvalue[1]

    def parseLine(self, line):
        if line.startswith("End Actor"):
            print("????")
            return
        key = line[:line.find("=")].strip()
        value = line[line.find("=")+1:].strip()
        self.keyvalues[key] = value

    def addChild(self, child):
        assert(not self.brush)
        self.brush = child

class Brush:
    def __init__(self, line):
        self.name = line.split("=")[-1]
        self.polygons = []

    def parseLine(self, line):
        pass

    def addChild(self, child):
        self.polygons.append(child)

def getActors(path):
    stack = []
    actors = []

    def parseBrushLine(line):
        pass

    def parsePolyLine(line):
        pass

    parseDict = {
        "Actor": Actor,
        "Brush": Brush
    }
    
    with open(path) as file:
        for line in file:
            words = line.split()
            if words and words[0] == "Begin":
                currentItem = words[1]
                if currentItem in parseDict:
                    currentObject = parseDict[currentItem](line)
                    stack.append(currentObject)
            
            if stack:
                stack[-1].parseLine(line)

            if words and words[0] == "End":
                currentItem = words[1]
                if currentItem in parseDict:
                    done = stack.pop()
                    if stack:
                        stack[-1].addChild(done)
                    else:
                        actors.append(done)

    return actors

def transformKeyValues(kvString):
    try:
        kvString = kvString[1:-1] # Remove brackets
        values = kvString.split(",")
        values = { v.split("=")[0] : float(v.split("=")[1]) for v in values }
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