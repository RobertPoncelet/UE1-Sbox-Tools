import colorsys
import glob
import hammer
import t3d_parsing as t3d
import halfedge_mesh
import os.path

# Maps Actor classname (not Entity classname) to the default input/output for that Entity
defaultIO = {
    "spellTrigger"  : hammer.EntityIO("OnTrigger", None, "Trigger", None, 0, None), # maxTimes should be deduced from the Actor
    "Mover"         : hammer.EntityIO("OnFullyOpen", None, "Toggle", None, 0, -1),
    "Counter"       : hammer.EntityIO("OnHitMax", None, "Add", 1, 0, -1),
    "Trigger"       : hammer.EntityIO("OnStartTouch", None, "Enable", None, 0, -1),
    "DiffindoVines" : hammer.EntityIO("OnBreak", None, "Break", None, 0, -1),
    "Ectoplasma"    : hammer.EntityIO("OnRemove", None, "Remove", None, 0, -1)
}

defaultIOAliases = {
    "DiffindoVines" : ["DiffindoRoots", "DiffindoWeb1", "DiffindoRope64", "DiffindoRope128"],
    "Ectoplasma" : ["EctoplasmaBIG", "Ectoblob"]
}

for key in defaultIOAliases:
    for alias in defaultIOAliases[key]:
        defaultIO[alias] = defaultIO[key]

models = None
def getModels():
    global models
    if not models:
        models = glob.glob("..\\hla_addon_content\\models\\*.vmdl")
        models = ["/".join(path.split("\\")[2:]).lower() for path in models] # this is necessary because this directory is not the same as the addon content directory
    return models

def isBuildable(actor):
    invalidClasses = [
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

def buildEntities(_actors, classes, numExistingEnts):
    global actors # Kinda hacky but too lazy to change it right now
    actors = _actors
    id = numExistingEnts
    mapname = os.path.splitext(os.path.basename(path))[0]
    for actor in actors:
        id += 1
        actor["_mapname"] = mapname
        newEnt = buildEntity(actor, id)
        if newEnt:
            classes.append(newEnt)

def buildEntity(actor, id):
    if not isBuildable(actor):
        return None
    elif not "Location" in actor:
        print("Weird actor: {} {}".format(actor["Class"], actor["Name"]))
        #return None
    
    ent = hammer.HammerClass("entity")
    ent.addProperty("id", str(id))

    # We now have the entity to create and the actor to create it from
    # We try each of these functions on the actor until we find a match
    # The entity is then confirmed as the type decided from that function
    buildFuncs = [buildCommon, buildLight, buildPointEnt, buildModel]
    for buildFunc in buildFuncs:
        if buildFunc(actor, ent):
            break

    if actor.brush:
        ent.brush = halfedge_mesh.Mesh.from_t3d_brush(actor.brush)
    
    return ent

def buildCommon(actor, ent):
    if actor["Class"] != "Brush":
        ent.addProperty("classname", actor["Class"])
    
    if "Location" in actor:
        ent.addProperty("origin", t3d.locationToOrigin(actor["Location"]))
        
    if "Rotation" in actor:
        ent.addProperty("angles", t3d.rotationToAngles(actor["Rotation"], -90.))
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

    buildIO(actor, ent)
    
    editor = hammer.HammerClass("editor")
    editor.addProperty("color", "255 128 128")
    editor.addProperty("visgroupshown", "1")
    editor.addProperty("visgroupautoshown", "1")
    ent.addClass(editor)
    return False # Entity isn't finished yet

def buildModel(actor, ent):
    modelEntityBuilders = [
        buildChest, 
        buildBean,
        buildWizardCard,
        buildMover, 
        buildDiffindoBarrier,
        buildEctoplasm,
        buildSpongifyPad, 
        buildSpongifyTarget,
        buildGnome,
        buildHorklumps,
        buildLumosGargoyle,
        buildMixingCauldron,
        buildKnight,
        buildNpc,
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
    if "LightRay" in actor["Class"]:
        ent.addProperty("disableshadows", 1)
        ent.addProperty("renderamt", 128)
        ent.addProperty("solid", 3)
    else:
        ent.addProperty("solid", 6)
    return True

def buildPointEnt(actor, ent):
    pointEntityBuilders = [        
        buildSkyCamera,
        buildPlayerStart,
        buildSecret,
        buildSpellTrigger,
        buildCounter,
        buildTemplate,
        buildSound,
        buildRelay,
    ]
    for func in pointEntityBuilders:
        if func(actor, ent):
            return True
    return False

def buildIO(actor, ent):
    if "Event" in actor:
        event = actor["Event"]
        global actors
        for other in actors:
            if actor["Class"] in defaultIO and other["Class"] in defaultIO and "Name" in other and "Tag" in other and other["Tag"] == event:
                thisIO = defaultIO[actor["Class"]]
                otherIO = defaultIO[other["Class"]]
                onceOnly = actor["bTriggerOnceOnly"] if "bTriggerOnceOnly" in actor else False
                onceOnly = onceOnly or (other["bTriggerOnceOnly"] if "bTriggerOnceOnly" in other else False)
                timesToFire = 1 if onceOnly else (otherIO.timesToFire if otherIO.timesToFire is not None else 0)
                ent.addOutput(thisIO.outputName, other["Name"], otherIO.inputName, 
                    otherIO.overrideParam, otherIO.delay, timesToFire)
    return False # Not done yet

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
            ent.addProperty("angles", t3d.rotationToAngles(actor["Rotation"], -90.))
            
    return True

def buildChest(actor, ent):
    if not actor["Class"].lower().startswith("chest"):
        return False
    ent.addProperty("classname", "tp_item_chest")
    ent.addProperty("skin_str", actor["Class"][len("Chest"):])
    numBeans = 0
    wizardcard = None
    for key in actor:
        if key.startswith("EjectedObjects") and "bean" in actor[key].lower():
            numBeans += 1
        if key.startswith("EjectedObjects") and "WC" in actor[key]:
            if actor[key].startswith("Class'"):
                wizardcard = actor[key][6:-1]
            else: # TODO: does this ever happen?
                wizardcard = actor[key][2:]
    if "iNumberOfBeans" in actor:
        numBeans += int(actor["iNumberOfBeans"])
    ent.addProperty("numbeans", numBeans)
    if wizardcard: ent.addProperty("wizardcard", wizardcard)
    
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
            ent.addProperty(outKey, t3d.rotationToAngles(actor[key]))
        if key == "BasePos" or "KeyPos" in key:
            outKey = key.lower().replace("(", "_").replace(")", "")
            ent.addProperty(outKey, t3d.locationToOrigin(actor[key]))
    return True
            
def buildDiffindoBarrier(actor, ent):
    if (actor["Class"] != "DiffindoVines" 
        and actor["Class"] != "DiffindoRoots"
        and actor["Class"] != "DiffindoWeb1"
        and "DiffindoRope" not in actor["Class"]):
        return False
    ent.addProperty("classname", "tp_ent_diffindobarrier")
    modelName = actor["Class"]
    modelPath = ("models/" + modelName + ".vmdl").lower()
    ent.addProperty("model", modelPath)
    return True

def buildEctoplasm(actor, ent):
    if ("Ectoplasma" not in actor["Class"]
        and "Ectoblob" != actor["Class"]):
        return False
    ent.addProperty("classname", "tp_ent_ectoplasm")
    modelName = actor["Class"]
    modelPath = ("models/" + modelName + ".vmdl").lower()
    ent.addProperty("model", modelPath)
    if "fShrinkTime" in actor:
        ent.addProperty("shrinktime", actor["fShrinkTime"])
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
    if actor["Class"] != "CauldronMixing":
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

def buildKnight(actor, ent):
    if actor["Class"] != "Knightspawn":
        return False
    ent.addProperty("classname", "tp_ent_knight")
    if "Limits" in actor:
        d = t3d.transformKeyValues(actor["Limits"])
        if "Max" in d:
            ent.addProperty("maxBeans", int(d["Max"]))
        if "Min" in d:
            ent.addProperty("minBeans", int(d["Min"]))
    if "Lives" in actor:
        ent.addProperty("lives", int(actor["Lives"]))
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