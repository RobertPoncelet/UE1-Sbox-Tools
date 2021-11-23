from collections import namedtuple
from dataclasses import dataclass
from shutil import copyfile
import argparse
import colorsys
import constants
import glob
import os.path
import sys
import multiprocessing as mp
import datamodel as dmx

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
        self.dmxConnections = []
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

    def getTemplateEntity(self):
        #e = dmx.load("template_entity.vmap").root #datamodel.add_element(None, "CMapEntity")
        # TODO: why does loading template_entity.vmap result in the wrong root element??
        e = dmx.load("test_input.vmap").root["world"]["children"][0]
        e["entity_properties"].clear()
        del(e["origin"])
        del(e["angles"])

        del(e["scales"])
        del(e["nodeID"])
        del(e["referenceID"])
        return e

    @dataclass
    class Connection:
        outputName: str
        targetName: str
        inputName: str
        overrideParam: str
        delay: float = 0.0
        timesToFire: int = -1
        targetType: int = 7 # TODO: is it ever anything else?

    def createDmxConnection(self, connection, elem):
        c = elem.datamodel.add_element(None, "DmeConnectionData")
        c["outputName"] = connection.outputName
        c["targetName"] = connection.targetName
        c["inputName"] = connection.inputName
        c["overrideParam"] = connection.overrideParam
        c["delay"] = connection.delay
        c["timesToFire"] = connection.timesToFire
        c["targetType"] = connection.targetType
        return c

    def toEntityElement(self):
        e = self.getTemplateEntity()

        props = dict(self.properties) # Make a copy so we can remove stuff

        if "origin" in props:
            e["origin"] = dmx.Vector3(props["origin"].split())
            del(props["origin"])
        if "angles" in props:
            e["angles"] = dmx.QAngle(props["angles"].split())
            del(props["angles"])
        if "scales" in props:
            e["scales"] = dmx.Vector3(props["scales"].split())
            del(props["scales"])
        if "id" in props:
            e["nodeID"] = int(props["id"])
            e["referenceID"] = dmx.uint64(props["id"])
            del(props["id"])

        # TODO: other default keyvalues

        for key in props:
            e["entity_properties"][key] = str(props[key])
        
        for c in self.dmxConnections:
            e["connectionsData"].append(self.createDmxConnection(c, e))

        return e
        
    def addOutput(self, outputName, target, targetInput, param, delay, maxTimes):
        if not any(c.className == "connections" for c in self.classes):
            self.addClass(HammerClass("connections"))
        for c in self.classes:
            if c.className == "connections":
                args = ["" if s is None else s for s in [target, targetInput, param, delay, maxTimes]]
                value = ",".join([str(s) for s in args])
                c.addProperty(outputName, value)
                break
        self.dmxConnections.append(self.Connection(outputName, target, targetInput, param, delay, maxTimes))
        
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

def transformKeyValues(rotation):
    try:
        rotation = rotation[1:-1] # Remove brackets
        values = rotation.split(",")
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
    
def buildEntities(path, classes, numExistingEnts):
    global actors 
    actors = getActors(path)
    id = numExistingEnts
    mapname = os.path.splitext(os.path.basename(path))[0]
    for actor in actors:
        id += 1
        actor["_mapname"] = mapname
        newEnt = buildEntity(actor, id)
        if newEnt is not None:
            classes.append(newEnt)

#========================================
# Start entity building functions
#========================================

# Maps Actor classname (not Entity classname) to the default input for that Entity
EntityIO = namedtuple("EntityIO", "output input param delay maxTimes")
defaultIO = {
    "spellTrigger" : EntityIO("OnTrigger", "Trigger", None, 0, None), # maxTimes should be deduced from the Actor
    "Mover" : EntityIO("OnFullyOpen", "Toggle", None, 0, -1),
    "Counter" : EntityIO("OnHitMax", "Add", 1, 0, -1),
    "Trigger" : EntityIO("OnStartTouch", "Enable", None, 0, -1)
}

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
        ent.addProperty("classname", "light_spot")
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
    if actor["Class"] != "Mover" and actor["Class"] != "ElevatorMover" and actor["Class"] != "LoopMover":
        return False
    ent.addProperty("classname", "tp_ent_door")
    ent.addProperty("model", "models/movers/" + actor["_mapname"] + "_" + actor["Name"] + ".vmdl")
    ent.addProperty("scales", "1 1 1") # Don't scale
    for key in actor:
        if (key == "SavedPos" or key == "SavedRot" # These aren't used AFAIK
            or key == "Rotation" or key == "PostScale"):
            continue
        if key == "BaseRot" or "KeyRot" in key:
            outKey = key.lower().replace("(", "_").replace(")", "")
            ent.addProperty(outKey, rotationToAngles(actor[key]))
        if key == "BasePos" or "KeyPos" in key:
            outKey = key.lower().replace("(", "_").replace(")", "")
            ent.addProperty(outKey, locationToOrigin(actor[key]))
    return True
            
def buildDiffindoBarrier(actor, ent):
    if (actor["Class"] != "DiffindoVines" 
        and actor["Class"] != "DiffindoRoots"
        and actor["Class"] != "DiffindoWeb"):
        return False
    ent.addProperty("classname", "tp_ent_diffindobarrier")
    modelName = actor["Class"]
    modelPath = ("models/" + modelName + ".vmdl").lower()
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
    ent.addProperty("scales", "1 1 1") # Don't scale the player!
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
    if spell == "Alohomora" : spell = "Alohamora" # Fix dumb "AlohOmora" typo in the original maps lol
    ent.addProperty("spelltype", spell)
    onceOnly = actor["bTriggerOnceOnly"] if "bTriggerOnceOnly" in actor else False
    if "Event" in actor:
        event = actor["Event"]
        global actors
        for other in actors:
            if other["Class"] in defaultIO and "Name" in other and "Tag" in other and other["Tag"] == event:
                ioInfo = defaultIO[other["Class"]]
                ent.addOutput("OnTrigger", other["Name"], ioInfo.input, ioInfo.param, ioInfo.delay, 1 if onceOnly else -1)
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
    ent.addProperty("model", "models/gen_fem_1.vmdl")
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
    modelName = actor["Class"]
    modelPath = ("models/" + modelName + ".vmdl").lower()
    if modelPath not in getModels():
        return False
    ent.addProperty("classname", "prop_static")
    ent.addProperty("fademindist", "-1")
    ent.addProperty("fadescale", "1")
    ent.addProperty("model", modelPath)
    ent.addProperty("skin", 0)
    ent.addProperty("solid", 3)
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

models = None
def getModels():
    global models
    if not models:
        models = glob.glob("..\\hla_addon_content\\models\\*.vmdl")
        models = ["/".join(path.split("\\")[2:]).lower() for path in models] # this is necessary because this directory is not the same as the addon content directory
    return models

def convertMapFile(path, format):
    if format == "dmx":
        extension = "vmap"
    else:
        extension = "vmf"
    out_path = path[:-3] + extension

    if not constants.OVERWRITE and os.path.isfile(out_path):
        print("Not overwriting " + out_map_path)
        return
    print("Processing " + path)
    if format == "vmf":
        convertMapFileToVMF(path, out_path)
    else: #elif format == "dmx":
        convertMapFileToDMX(path, out_path)

    # Copy it from $GAME/maps to hla_addon_content/maps
    copy_path = "..\\hla_addon_content\\maps" #os.path.join(constants.ROOT_PATH, "hla_addon_content\\maps")
    copy_path = os.path.join(copy_path, os.path.basename(out_path))
    copyfile(out_path, copy_path)
    print("Finished copying " + out_path + " to " + copy_path)

def convertMapFileToDMX(path, out_path):
    dm = dmx.load("template_map.vmap")

    globalClasses = []
    buildEntities(path, globalClasses, 0)
    for ent in globalClasses:
        dm.root["world"]["children"].append(ent.toEntityElement())

    dm.write(out_path, "keyvalues2", 4)

def convertMapFileToVMF(path, out_path):
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

    with open(out_path, "w") as f:
        for c in globalClasses:
            c.write(f, 0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a T3D file to a VMF or VMAP.')
    parser.add_argument('--maps', type=str, default="../hp*/maps/*.t3d",
                        help='Glob specifying which maps to convert.')
    parser.add_argument('--format', default="dmx",
                        help='Output format (DMX or VMF).')

    args = parser.parse_args()

    args.format = args.format.lower()
    if args.format != "dmx" and args.format != "vmf":
        print("Invalid format " + args.format + "; choose DMX or VMF")
        quit()

    maps = glob.glob(args.maps, recursive=True)

    if len(maps) == 0:
        print("No files match " + args.maps)
        quit()

    maps_args = [(m, args.format) for m in maps]

    with mp.Pool(processes=constants.NUM_CORES) as pool:
        pool.starmap(convertMapFile, maps_args)
