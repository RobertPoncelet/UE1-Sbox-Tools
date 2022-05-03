import constants

def getActors(path):
    currentActor = {}
    actors = []
    skip = True
    with open(path) as file:
        for line in file:
            if line.startswith("Begin Actor"):
                skip = False
                words = line.split()[2:]
                for word in words:
                    keyvalue = word.split("=")
                    if (len(keyvalue) != 2):
                        print(line)
                        raise SyntaxError("T3D file shouldn't look like this")
                    currentActor[keyvalue[0]] = keyvalue[1]
                continue
            if line == "End Actor\n" and not skip:
                actors.append(currentActor)
                currentActor = {}
                skip = True
                continue
            if skip:
                continue
            key = line[:line.find("=")].strip()
            value = line[line.find("=")+1:].strip()
            currentActor[key] = value
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