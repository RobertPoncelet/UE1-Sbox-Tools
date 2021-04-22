import colorsys
import constants
import glob
import os.path
import sys

class HammerClass:
    className = ""
    properties = {}
    classes = []
    f = None
    indentLevel = 0
    
    def __init__(self, inName):
        self.className = inName
        self.properties = {}
        self.classes = []
        self.f = None
        self.indentLevel = 0
        
    def writeLine(self, string):
        for i in range(0, self.indentLevel):
            self.f.write("\t")
        self.f.write(string + "\n")
        
    def addProperty(self, name, value):
        self.properties[name] = value
        
    def addClass(self, hClass):
        self.classes.append(hClass)
        
    def output(self, inFile, inIndentLevel):
        self.f = inFile
        self.indentLevel = inIndentLevel
        self.writeLine(self.className)
        self.writeLine("{")
        self.indentLevel += 1
        for p in self.properties:
            pString = "\"{0}\" \"{1}\"".format(p, self.properties[p])
            self.writeLine(pString)
        for c in self.classes:
            c.output(self.f, self.indentLevel)
        self.indentLevel -= 1
        self.writeLine("}")
        
def buildBrushes(geo):
     brushNum = 0
     brushes = []
     while geo.findPrimGroup("brush" + str(brushNum)) is not None:
        pGroup = geo.findPrimGroup("brush" + str(brushNum))
        brushes.append(buildBrush(pGroup, brushNum + 2))
        brushNum += 1
     for i in range(0, 1500):
        pGroup = geo.findPrimGroup("Model" + str(i))
        if pGroup is not None:
            #print("Found Model" + str(i))
            brushes.append(buildBrush(pGroup, brushNum + 2))
            brushNum += 1
     # Ugly bit to assign side IDs
     sideid = 0
     for brush in brushes:
        for i in xrange(0, len(brush.classes)-1):
            side = brush.classes[i]
            side.properties[0] = ("id", str(sideid))
            sideid += 1
     return brushes 
    
def buildBrush(prims, id):
    brush = HammerClass("solid")
    brush.addProperty("id", str(id))
    for prim in prims.prims():
        brush.addClass(buildSide(prim))
    editor = HammerClass("editor")
    try:
        Cd = prims.prims()[0].floatListAttribValue("Cd")
    except IndexError:
        Cd = [0.5, 0.5, 0.5]
    c0 = Cd[0] * 256
    c1 = Cd[1] * 256
    c2 = Cd[2] * 256
    editor.addProperty("color", "{0} {1} {2}".format(c0, c1, c2))
    editor.addProperty("visgroupshown", "1")
    editor.addProperty("visgroupautoshown", "1")
    brush.addClass(editor)
    return brush

def buildSide(face):
    side = HammerClass("side")
    side.addProperty("id", "ERROR") # We assign this later
    # Do we need to check for collinearity here? probably not
    # Take the first vertex and two others that are far away from the first and each other
    v0 = face.vertices()[0]
    v1 = face.vertices()[1]
    v2 = face.vertices()[2]
    #verts = list(face.vertices())[1:]
    #p0 = v0.point().position()
    #distances = [(v.point().position().distanceTo(p0), v) for v in verts]
    #v1 = max(distances,key=itemgetter(0))[1]
    #verts.remove(v1)
    #p0p1 = v1.point().position() - p0
    #crosses = [((v.point().position() - p0).cross(p0p1).length(), v) for v in verts]
    #v2 = max(crosses,key=itemgetter(0))[1]
    # Convert those to strings
    v0 = vertToString(v0, True)
    v1 = vertToString(v1, True)
    v2 = vertToString(v2, True)
    side.addProperty("plane", "{0} {1} {2}".format(v0, v1, v2))
    material = ""
    #inner = face.geometry().findPrimGroup("inner")
    #if inner is not None and inner.contains(face):
        #if normal.isAlmostEqual(up) or normal.isAlmostEqual(-up):
        #    material = "DEV/DEV_MEASUREGENERIC01B"
        #else:
        #    material = "DEV/DEV_MEASUREWALL01A"
    #else:
    #    material = "TOOLS/TOOLSNODRAW"
    try:
        mtl = face.attribValue("shop_materialpath").rstrip(string.digits)
        mtl = mtl.split("/")[2]
        mtl = mtl.split(".")
        material = "hp/{}/texture/{}".format(mtl[0], mtl[2])
    except IndexError:
        material = "TOOLS/TOOLSNODRAW"
    side.addProperty("material", material)
    #u, v = texAxes(face)
    u = texAxis_old(face, False)
    v = texAxis_old(face, True)
    side.addProperty("uaxis", "[{0} {1} {2} {3}] {4}"
        .format(u[0], u[1], u[2], u[3], 0.5))    
    side.addProperty("vaxis", "[{0} {1} {2} {3}] {4}"
        .format(v[0], v[1], v[2], v[3], 0.5))
    side.addProperty("rotation", "0")
    side.addProperty("lightmapscale", "16")
    side.addProperty("smoothing_groups", "0")
    return side
    
def texAxis_old(face, useV):
    normal = face.normal()
    up = hou.Vector3(0.0, 0.0, 1.0)
    axis = up
    if axis.isAlmostEqual(normal) or axis.isAlmostEqual(-normal):
        axis = hou.Vector3(1.0, 0.0, 0.0)
    u = axis.cross(normal)
    v = u.cross(normal)
    if (useV):
        return [v[0], v[1], v[2], 0]
    else:
        return [u[0], u[1], u[2], 0]
        
def texAxes(face):
    # Get the 3 points in both spaces
    vtxA = face.vertices()[0]
    pA = np.array(vtxA.point().position())
    uA = np.array(vtxA.floatListAttribValue("uvv")[:2])
    vtxB = face.vertices()[1]
    pB = np.array(vtxB.point().position())
    uB = np.array(vtxB.floatListAttribValue("uvv")[:2])
    vtxC = face.vertices()[2]
    pC = np.array(vtxC.point().position())
    uC = np.array(vtxC.floatListAttribValue("uvv")[:2])
    # Get the 2 basis vectors in each space
    pAB = pB - pA
    uAB = uB - uA
    pAC = pC - pA
    uAC = uC - uA
    # Find A to the UV origin in terms of the basis vectors
    uAO = -uA 
    basis = np.array([uAB, uAC])
    try:
        coeffs = np.linalg.solve(basis, uAO)
    except np.linalg.LinAlgError:
        coeffs = np.array([1.0, 0.0]) # I guess?
    # Use these coefficients to find the same point in 3D space
    pO = pA + (coeffs[0] * pAB) + (coeffs[1] * pAC)
    # Repeat for the UV axes
    uU = np.array([1.0, 0.0])
    uV = np.array([0.0, 1.0])
    try:
        Ucoeffs = np.linalg.solve(basis, uU)
    except np.linalg.LinAlgError:
        Ucoeffs = np.array([1.0, 0.0])
    try:
        Vcoeffs = np.linalg.solve(basis, uV)
    except np.linalg.LinAlgError:
        Vcoeffs = np.array([0.0, 1.0])
    pU = pA + (Ucoeffs[0] * pAB) + (Ucoeffs[1] * pAC)
    pV = pA + (Vcoeffs[0] * pAB) + (Vcoeffs[1] * pAC)
    # Also find pO in terms of normalized pU and pV for the offsets
    pUn = pU/np.linalg.norm(pU) #np.sqrt((pU**2).sum())
    pVn = pV/np.linalg.norm(pV) #np.sqrt((pV**2).sum())
    pWn = np.cross(pUn, pVn)
    pBasis = np.array([pUn, pVn, pWn])
    try:
        pOffsets = np.linalg.solve(pBasis, pO)
    except np.linalg.LinAlgError:
        pOffsets = np.array([0.0, 0.0, 0.0])
    # Sort values for return!
    uAxis = [pUn[0], pUn[1], pUn[2], pOffsets[0]]
    uAxis = [round(x) for x in uAxis]
    uAxis[3] = math.fmod(uAxis[3], 256)
    vAxis = [pVn[0], pVn[1], pVn[2], pOffsets[1]]
    vAxis = [round(x) for x in vAxis]
    vAxis[3] = math.fmod(vAxis[3], 256)
    return uAxis, vAxis
    
#def coefficients(target, a, b):
    # Return j and k given target == j*a + k*b
     
def vertToString(vert, brackets):
    return pointToString(vert.point(), brackets)
    
def pointToString(point, brackets):
    pos = point.position()
    if brackets:
        return "({0} {1} {2})".format(int(pos[0]), int(pos[1]), int(pos[2]))
    else:
        return "{0} {1} {2}".format(int(pos[0]), int(pos[1]), int(pos[2]))
    
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
                        assert(false)
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
    #print(actors)
    return actors

def locationToOrigin(location):
    loc = location[1:-1] # Remove brackets
    dims = loc.split(",")
    pos = [0.0, 0.0, 0.0]
    for d in dims:
        if d[0] == "X":
            pos[0] = float(d[2:])
        elif d[0] == "Y":
            pos[1] = float(d[2:])
        elif d[0] == "Z":
            pos[2] = float(d[2:])
    return "{} {} {}".format(pos[1]*constants.SCALE, pos[0]*constants.SCALE, pos[2]*constants.SCALE) # X and Y are swapped

def rotationToAngles(rotation, yawOffset=0.):
    rotation = rotation[1:-1] # Remove brackets
    values = rotation.split(",")
    values = { v.split("=")[0] : v.split("=")[1] for v in values }
    angles = [0.0, 0.0, -180.0]
    factor = -360. / 65536. # Unreal rotations seem to be encoded as 16-bit ints
    for key in values:
        if key == "Pitch":
            angles[0] = float(values[key]) * factor - 180.
        elif key == "Yaw":
            angles[2] = float(values[key]) * factor - 180. + yawOffset
        elif key == "Roll":
            angles[1] = float(values[key]) * factor - 180.
    angles = [angles[1], angles[2], angles[0]] # Hammer stores rotations as Y Z X
    return "{} {} {}".format(angles[0], angles[1], angles[2])
    
def buildEntities(path, classes, numExistingEnts):
    actors = getActors(path)
    id = numExistingEnts
    for actor in actors:
        id += 1
        newEnt = buildEntity(actor, id)
        if newEnt is not None:
            classes.append(newEnt)

# Start entity building functions

def buildLight(actor, ent):
    if not (actor["Class"] == "Light"
            or actor["Class"] == "Spotlight"
            or actor["Class"] == "Torch_light"):
        return False
    ent.addProperty("classname", "light_omni")

    radius = float(actor["LightRadius"]) if "LightRadius" in actor else 256.
    radius *= 32. # Hacky estimate
    ent.addProperty("range", radius)

    brightness = float(actor["LightBrightness"]) if "LightBrightness" in actor else 64.
    brightness /= 256.
    ent.addProperty("brightness", brightness * 4.) # Also a hacky estimate
    
    h = float(actor["LightHue"]) if "LightHue" in actor else 0.
    h /= 256.
    s = float(actor["LightSaturation"]) if "LightSaturation" in actor else 255.
    s = 1. - (s / 256.)
    v = 0.75 #brightness
    colour = colorsys.hsv_to_rgb(h, s, v)
    colour = tuple(int(c*256.0) for c in colour)
    ent.addProperty("color", "{} {} {}".format(colour[0], colour[1], colour[2]))

    ent.addProperty("castshadows", 2) # Baked shadows only
    ent.addProperty("renderspecular", 0) # None of that fancy PBR in 2002
    ent.addProperty("baked_light_indexing", 0)

    if actor["Class"] == "Spotlight":
        ent.addProperty("classname", "light_spot_") # Change the name to avoid the importer trying to convert from Source 1
        cone = float(actor["LightCone"]) if "LightCone" in actor else 128.
        angle = (cone / 256.) * 90.
        ent.addProperty("innerconeangle", angle/2.)
        ent.addProperty("outerconeangle", angle)
        # UE1 and Source 2 have different forward axes
        if "Rotation" in actor:
            ent.addProperty("angles", rotationToAngles(actor["Rotation"], -90.))
            
    return True

def buildModel(actor, ent):
    global models
    modelName = actor["Class"]
    # Hack for chests
    if modelName[:5] == "Chest":
        modelName = modelName[5:] + "Chest"
        ent.addProperty("scales", "2 2 2")
    modelPath = ("models\\" + modelName + ".vmdl").lower()
    if modelPath not in models:
        return False
    ent.addProperty("classname", "prop_static")
    ent.addProperty("fademindist", "-1")
    ent.addProperty("fadescale", "1")
    ent.addProperty("model", modelPath)
    ent.addProperty("skin", 0)
    ent.addProperty("solid", 6)
    return True

def buildPlayerStart(actor, ent):
    if actor["Class"] != "PlayerStart":
        return False
    ent.addProperty("classname", "info_player_start")
    return True

def buildCommon(actor, ent):
    ent.addProperty("classname", actor["Class"] if "Class" in actor else "info_target")
    
    if "Location" in actor:
        ent.addProperty("origin", locationToOrigin(actor["Location"]))
    if "Rotation" in actor:
        ent.addProperty("angles", rotationToAngles(actor["Rotation"]))
    if "DrawScale" in actor:
        scale = actor["DrawScale"]
        ent.addProperty("scales", "{} {} {}".format(scale, scale, scale))
    if "Name" in actor:
        ent.addProperty("targetname", actor["Name"])
    
    editor = HammerClass("editor")
    editor.addProperty("color", "255 128 128")
    editor.addProperty("visgroupshown", "1")
    editor.addProperty("visgroupautoshown", "1")
    ent.addClass(editor)
    return False # Entity isn't finished yet
        
def buildEntity(actor, id):
    if actor["Class"] == "Brush":
        return None # We're importing level geometry in a different way
    elif not "Location" in actor:
        print("Weird actor: {} {}".format(actor["Class"], actor["Name"]))
        #return None
    
    ent = HammerClass("entity")
    ent.addProperty("id", str(id))

    # We now have the entity to create and the actor to create it from
    # We try each of these functions on the actor until we find a match
    # The entity is then confirmed as the type decided from that function
    buildFuncs = [buildCommon, buildLight, buildModel, buildPlayerStart]
    for buildFunc in buildFuncs:
        if buildFunc(actor, ent):
            break
    
    return ent

def convertMapFile(path):
    #node = hou.pwd()
    #geo = node.geometry()

    globalClasses = []

    versioninfo = HammerClass("versioninfo")
    versioninfo.addProperty("editorversion", "400")
    versioninfo.addProperty("editorbuild", "6412")
    versioninfo.addProperty("mapversion", "1")
    versioninfo.addProperty("formatversion", "100")
    versioninfo.addProperty("prefab", "0")
    globalClasses.append(versioninfo)

    visgroups = HammerClass("visgroups")
    globalClasses.append(visgroups)

    viewsettings = HammerClass("viewsettings")
    viewsettings.addProperty("bSnapToGrid", "1")
    viewsettings.addProperty("bShowGrid", "1")
    viewsettings.addProperty("bShowLogicalGrid", "0")
    viewsettings.addProperty("nGridSpacing", "32")
    viewsettings.addProperty("bShow3DGrid", "0")
    globalClasses.append(viewsettings)

    world = HammerClass("world")
    world.addProperty("id", "1")
    world.addProperty("mapversion", "1")
    world.addProperty("classname", "worldspawn")
    world.addProperty("skyname", "sky_day01_01")
    world.addProperty("maxpropscreenwidth", "-1")
    world.addProperty("detailvbsp", "detail.vbsp")
    world.addProperty("detailmaterial", "detail/detailsprites")
    #world.classes = buildBrushes(geo) # Don't bother with brushes
    globalClasses.append(world)

    numExistingEnts = len(world.classes) + 1
    buildEntities(path, globalClasses, numExistingEnts)

    cameras = HammerClass("cameras")
    cameras.properties["activecamera"] = "-1"
    globalClasses.append(cameras)

    cordon = HammerClass("cordon")
    cordon.properties["mins"] = "(-1024 -1024 -1024)"
    cordon.properties["maxs"] = "(1024 1024 1024)"
    cordon.properties["active"] = "0"
    globalClasses.append(cordon)

    out_path = path[:-3] + "vmf"
    with open(out_path, "w") as f:
        for c in globalClasses:
            c.output(f, 0)

glob_path = sys.argv[1] if len(sys.argv) > 1 else "../hp*/maps/*.t3d"
maps = glob.glob(glob_path, recursive=True)
models = glob.glob("..\\hla_addon_content\\models\\*.vmdl")
models = ["\\".join(path.split("\\")[2:]).lower() for path in models] # this is necessary because this directory is not the same as the addon content directory

#maps = [maps[0]] # remove for all maps

for map_path in maps:
    out_map_path = map_path[:-3] + "vmf"
    if not constants.OVERWRITE and os.path.isfile(out_map_path):
        print("Not overwriting " + out_map_path)
        continue
    print("Processing " + map_path)
    convertMapFile(map_path)
