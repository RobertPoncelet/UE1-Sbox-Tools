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
        
    def addOutput(self, outputName, target, targetInput, param, delay, maxTimes):
        if not any(c.className == "connections" for c in self.classes):
            self.addClass(HammerClass("connections"))
        for c in self.classes:
            if c.className == "connections":
                args = ["" if s is None else s for s in [target, targetInput, param, delay, maxTimes]]
                value = ",".join([str(s) for s in args])
                c.addProperty(outputName, value)
                break
        
    def write(self, inFile, inIndentLevel):
        self.f = inFile
        self.indentLevel = inIndentLevel
        self.writeLine(self.className)
        self.writeLine("{")
        self.indentLevel += 1
        for p in self.properties:
            pString = "\"{0}\" \"{1}\"".format(p, self.properties[p])
            self.writeLine(pString)
        for c in self.classes:
            c.write(self.f, self.indentLevel)
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
    return "{} {} {}".format(pos[0]*constants.SCALE, -pos[1]*constants.SCALE, pos[2]*constants.SCALE) # Y is flipped

def rotationToAngles(rotation, yawOffset=0.):
    rotation = rotation[1:-1] # Remove brackets
    values = rotation.split(",")
    values = { v.split("=")[0] : float(v.split("=")[1]) for v in values }
    angles = [0., 0., 0.]
    factor = -360. / 65536. # Unreal rotations seem to be encoded as 16-bit ints
    for key in values:
        if key == "Pitch":
            angles[0] = values[key] * factor * -1. - 180.
        elif key == "Yaw":
            angles[1] = values[key] * factor - 180. + yawOffset
        elif key == "Roll":
            angles[2] = values[key] * factor - 180.
    #angles = [angles[1], angles[2], angles[0]] # Hammer stores rotations as Y Z X
    return "{} {} {}".format(angles[0], angles[1], angles[2])
    
def buildEntities(path, classes, numExistingEnts):
    global actors 
    actors = getActors(path)
    id = numExistingEnts
    for actor in actors:
        id += 1
        newEnt = buildEntity(actor, id)
        if newEnt is not None:
            classes.append(newEnt)

# Start entity building functions

def buildSprite(actor, ent):
    if not actor["Class"] == "candleflame":
        return False
    ent.addProperty("classname", "env_sprite")
    ent.addProperty("model", "hp_fx_general_candlef.vmat")
    return True

def buildLight(actor, ent):
    if buildSprite(actor, ent):
        return True
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

def buildChest(actor, ent):
    if not actor["Class"].startswith("Chest"):
        return False
    ent.addProperty("classname", "tp_item_chest")
    numBeans = 0
    wizardcard = None
    for key in actor:
        if key.startswith("EjectedObjects") and "bean" in actor[key].lower():
            numBeans += 1
        if key.startswith("EjectedObjects") and "WC" in actor[key]:
            wizardcard = actor[key][2:]
    ent.addProperty("numbeans", numBeans)
    if wizardcard: ent.addProperty("wizardcard", wizardcard)
    
    # For some reason chests have a different rotation??
    if "Rotation" in actor:
        ent.addProperty("angles", rotationToAngles(actor["Rotation"]))
    else:
        ent.addProperty("angles", "0 180 0")
    return True

def buildBean(actor, ent):
    if not actor["Class"].lower().endswith("bean"):
        return False
    ent.addProperty("classname", "tp_item_bean")
    ent.addProperty("usephysics", "0")
    ent.addProperty("scales", "1 1 1")
    return True
    
def buildWizardCard(actor, ent):
    if not actor["Class"].startswith("WC"):
        return False
    ent.addProperty("classname", "tp_item_wizardcard")
    ent.addProperty("usephysics", "0")
    ent.addProperty("scales", "1 1 1")
    ent.addProperty("wizardname", actor["Class"][2:])
    return True
    
def buildMover(actor, ent):
    if actor["Class"] != "Mover":
        return False
    ent.addProperty("classname", "tp_ent_door")
    for key in actor:
        if (key == "SavedPos" or key == "SavedRot" # These aren't used AFAIK
            or key == "Rotation" or key == "PostScale"):
            continue
        if "Rot" in key:
            outKey = key.lower().replace("(", "_").replace(")", "")
            ent.addProperty(outKey, rotationToAngles(actor[key]))
        elif "Pos" in key:
            outKey = key.lower().replace("(", "_").replace(")", "")
            ent.addProperty(outKey, locationToOrigin(actor[key]))
    return True
            
def buildDiffindoBarrier(actor, ent):
    if actor["Class"] != "DiffindoVines" and actor["Class"] != "DiffindoRoots":
        return False
    ent.addProperty("classname", "tp_ent_diffindobarrier")
    modelName = actor["Class"]
    modelPath = ("models\\" + modelName + ".vmdl").lower()
    ent.addProperty("model", modelPath)
    return True
    
def buildSpongifyPad(actor, ent):
    if actor["Class"] != "SpongifyPad":
        return False
    ent.addProperty("classname", "tp_ent_spongifypad")
    if "Event" in actor:
        event = actor["Event"]
        global actors
        for other in actors:
            if other["Class"] == "SpongifyTarget" and other["Tag"] == event and "Name" in other:
                ent.addProperty("target", other["Name"])
    if "fTimeToHitTarget" in actor:
        ent.addProperty("jumpduration", actor["fTimeToHitTarget"])
    return True
    
def buildSpongifyTarget(actor, ent):
    if actor["Class"] != "SpongifyTarget":
        return False
    ent.addProperty("classname", "info_target")
    return True

def buildGnome(actor, ent):
    if actor["Class"] != "GNOME":
        return False
    ent.addProperty("classname", "tp_npc_gnome")
    return True
    
def buildHorklumps(actor, ent):
    if actor["Class"] != "Horklumps":
        return False
    ent.addProperty("classname", "tp_npc_horklumps")
    return True
    
def buildLumosGargoyle(actor, ent):
    if actor["Class"] != "gargoyle":
        return False
    ent.addProperty("classname", "tp_npc_gargoyle")
    return True
    
def buildMixingCauldron(actor, ent):
    if actor["Class"] != "SkyZoneInfo":
        return False
    ent.addProperty("classname", "tp_ent_mixingcauldron")
    return True
    
def buildSkyCamera(actor, ent):
    if actor["Class"] != "SkyZoneInfo":
        return False
    ent.addProperty("classname", "sky_camera")
    return True
    
def buildPlayerStart(actor, ent):
    if actor["Class"] != "Harry":
        return False
    ent.addProperty("classname", "info_player_start")
    return True
    
def buildSecret(actor, ent):
    if actor["Class"] != "SecretAreaMarker":
        return False
    ent.addProperty("classname", "tp_ent_secretarea")
    radius = actor["CollisionRadius"] if "CollisionRadius" in actor else 64.
    height = actor["CollisionHeight"] if "CollisionHeight" in actor else 64.
    ent.addProperty("radius", radius)
    ent.addProperty("height", height)
    return True
    
def buildSpellTrigger(actor, ent):
    if actor["Class"] != "spellTrigger":
        return False
    ent.addProperty("classname", "tp_spelltrigger")
    spell = actor["eVulnerableToSpell"][6:] if "eVulnerableToSpell" in actor else "Alohamora"
    ent.addProperty("spelltype", spell)
    onceOnly = actor["bTriggerOnceOnly"] if "bTriggerOnceOnly" in actor else False
    if "Event" in actor:
        event = actor["Event"]
        global actors
        for other in actors:
            if other["Class"] == "Counter" and other["Tag"] == event and "Name" in other:
                ent.addOutput("OnTrigger", other["Name"], "Add", 1, 0, 1 if onceOnly else -1)
    return True
    
def buildCounter(actor, ent):
    if actor["Class"] != "Counter":
        return False
    ent.addProperty("classname", "math_counter")
    return True
    
def buildNpc(actor, ent):
    name = actor["Class"]
    isNpcName = (name.startswith("G") and (name[1:].startswith("Fem")
        or name[1:].startswith("Male") or name[1:].startswith("OldMale")))
    if not isNpcName:
        return False
    ent.addProperty("classname", "tp_npc_generic")
    ent.addProperty("model", "models\\gen_fem_1.vmdl")
    return True
    
def buildTemplate(actor, ent):
    if actor["Class"] != "SpawnThingy" and actor["Class"] != "InvisibleSpawn":
        return False
    ent.addProperty("classname", "point_template")
    return True
    
def buildSound(actor, ent):
    if actor["Class"] != "Sound_FX":
        return False
    ent.addProperty("classname", "ambient_generic")
    return True
    
def buildRelay(actor, ent):
    if actor["Class"] != "Dispatcher":
        return False
    ent.addProperty("classname", "logic_relay")
    return True
    
def buildSoundscape(actor, ent):
    if actor["Class"] != "AmbientSound":
        return False
    ent.addProperty("classname", "env_soundscape")
    soundscape = actor["AmbientSound"] if "AmbientSound" in actor else "ERROR"
    ent.addProperty("soundscape", soundscape)
    return True

def buildModel(actor, ent):
    modelEntityBuilders = [
        buildChest, 
        buildBean,
        buildWizardCard,
        buildMover, 
        buildDiffindoBarrier, 
        buildSpongifyPad, 
        buildSpongifyTarget,
        buildGnome,
        buildHorklumps,
        buildLumosGargoyle,
        buildMixingCauldron,
        buildSkyCamera,
        buildPlayerStart,
        buildSecret,
        buildSpellTrigger,
        buildCounter,
        buildNpc,
        buildTemplate,
        buildSound,
        buildRelay,
    ]
    for func in modelEntityBuilders:
        if func(actor, ent):
            return True
        
    # Otherwise, must be a generic model
    global models
    modelName = actor["Class"]
    modelPath = ("models\\" + modelName + ".vmdl").lower()
    if modelPath not in models:
        return False
    ent.addProperty("classname", "prop_static")
    ent.addProperty("fademindist", "-1")
    ent.addProperty("fadescale", "1")
    ent.addProperty("model", modelPath)
    ent.addProperty("skin", 0)
    ent.addProperty("solid", 6)
    if actor["Class"] == "LightRay":
        ent.addProperty("disableshadows", 1)
        ent.addProperty("renderamt", 128)
    return True

def buildCommon(actor, ent):
    ent.addProperty("classname", actor["Class"] if "Class" in actor else "info_target")
    
    if "Location" in actor:
        ent.addProperty("origin", locationToOrigin(actor["Location"]))
        
    if "Rotation" in actor:
        ent.addProperty("angles", rotationToAngles(actor["Rotation"], -90.))
    else:
        ent.addProperty("angles", "0 90 0")
        
    if "DrawScale" in actor:
        scale = actor["DrawScale"]
        ent.addProperty("scales", "{} {} {}".format(scale, scale, scale))
    else:
        ent.addProperty("scales", "1.5 1.5 1.5") # Weird default but ok
        
    if "Name" in actor:
        ent.addProperty("targetname", actor["Name"])
    else:
        print("No name for actor!")
    
    editor = HammerClass("editor")
    editor.addProperty("color", "255 128 128")
    editor.addProperty("visgroupshown", "1")
    editor.addProperty("visgroupautoshown", "1")
    ent.addClass(editor)
    return False # Entity isn't finished yet

def isBuildable(actor):
    invalidClasses = [
        "Brush", # We're importing level geometry in a different way
        "PlayerStart", 
        "ZoneInfo", 
        "HarryToGoyleTrigger", 
        "BlockAll", 
        "PopupTrigger",
        "SpellLessonInterpolationPoint",
        "CutMark",
        "CutScene",
        "SmartStart",
        "TriggerChangeLevel",
        "navShortcut",
        "SavePoint",
        "Speciallit",
        "BlockPlayer",
        
        # The following class names *may* be implemented at some point
        "Darklight",
        "CutScene",
        "CutCameraPos",
        "PatrolPoint",
        "Trigger",
        "NewMusicTrigger",
        "CreatureGenerator",
        "InterpolationPoint",
        "LumosSparkles",
        "LumosTrigger",
        "TargetPoint", # particularly this one, used for gnome throw targeting
        "Despawner", # and this one, used for despawning gnomes when thrown
    ]
    if actor["Class"] in invalidClasses:
        return False
    return True        
        
def buildEntity(actor, id):
    if not isBuildable(actor):
        return None
    elif not "Location" in actor:
        print("Weird actor: {} {}".format(actor["Class"], actor["Name"]))
        #return None
    
    ent = HammerClass("entity")
    ent.addProperty("id", str(id))

    # We now have the entity to create and the actor to create it from
    # We try each of these functions on the actor until we find a match
    # The entity is then confirmed as the type decided from that function
    buildFuncs = [buildCommon, buildLight, buildModel]
    for buildFunc in buildFuncs:
        if buildFunc(actor, ent):
            break
    
    return ent
    
def addExtraEntity(ent):
    global globalClasses
    globalClasses.append(ent)

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
            c.write(f, 0)

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
