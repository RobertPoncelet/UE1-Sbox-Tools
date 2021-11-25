from dataclasses import dataclass
import datamodel as dmx

@dataclass
class EntityIO:
    outputName: str
    targetName: str
    inputName: str
    overrideParam: str
    delay: float = 0.0
    timesToFire: int = -1
    targetType: int = 7 # TODO: is it ever anything else?

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

    def getTemplateElement(self, datamodel):
        e = datamodel.add_element(None, "CMapEntity")
        e["children"] = dmx.make_array(None, dmx.Element)
        e["editorOnly"] = False
        e["force_hidden"] = False
        e["transformLocked"] = False
        e["variableTargetKeys"] = dmx.make_array(None, str)
        e["variableNames"] = dmx.make_array(None, str)
        relayPlugData = datamodel.add_element(None, "DmePlugList")
        relayPlugData["names"] = dmx.make_array(None, str)
        relayPlugData["dataTypes"] = dmx.make_array(None, int)
        relayPlugData["plugTypes"] = dmx.make_array(None, int)
        relayPlugData["descriptions"] = dmx.make_array(None, str)
        e["relayPlugData"] = relayPlugData
        e["connectionsData"] = dmx.make_array(None, dmx.Element)
        e["entity_properties"] = datamodel.add_element(None, "EditGameClassProps")
        e["hitNormal"] = dmx.Vector3([0, 0, 1])
        e["isProceduralEntity"] = False

        return e

    def createDmxConnection(self, connection, datamodel):
        c = datamodel.add_element(None, "DmeConnectionData")
        c["outputName"] = str(connection.outputName)
        c["targetName"] = str(connection.targetName)
        c["inputName"] = str(connection.inputName)
        c["overrideParam"] = str(connection.overrideParam) if connection.overrideParam else ""
        c["delay"] = float(connection.delay)
        c["timesToFire"] = int(connection.timesToFire)
        c["targetType"] = int(connection.targetType)
        return c

    def toEntityElement(self, datamodel):
        e = self.getTemplateElement(datamodel)

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
            e["connectionsData"].append(self.createDmxConnection(c, datamodel))

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
        self.dmxConnections.append(EntityIO(outputName, target, targetInput, param, delay, maxTimes))
        
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