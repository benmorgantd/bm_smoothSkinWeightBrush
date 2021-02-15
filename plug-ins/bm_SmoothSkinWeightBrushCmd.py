import sys

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omAnim


def maya_useNewAPI():
    pass


class bmSmoothSkinWeightsBrushCmd(om.MPxCommand):
    COMMAND_NAME = 'bmSmoothSkinWeightsBrushCmd'
    undoQueue = []
    dagPath = om.MDagPath()
    component = om.MObject()
    neighborComponents = om.MObject()
    skinClusterMObject = om.MObject()
    vertexId = None
    strength = 1.0
    numVertexNeighbors = 0

    def __init__(self):
        super(bmSmoothSkinWeightsBrushCmd, self).__init__()

    @classmethod
    def isUndoable(cls):
        return True

    @classmethod
    def hasSyntax(cls):
        return True

    @classmethod
    def syntax(cls):
        _syntax = om.MSyntax()
        # vertex Id
        _syntax.addArg(om.MSyntax.kLong)
        # strength
        _syntax.addArg(om.MSyntax.kDouble)
        # shape name
        _syntax.addArg(om.MSyntax.kString)
        # skin cluster name
        _syntax.addArg(om.MSyntax.kString)

        return _syntax

    @classmethod
    def getVertexNeighbors(cls, dag, components):
        itVerts = om.MItMeshVertex(dag, components)
        neighboringVerts = set()
        numNeighbors = 0

        while not itVerts.isDone():
            neighbors = itVerts.getConnectedVertices()
            numNeighbors = len(neighbors)
            neighboringVerts.update(neighbors)
            break

        sel = om.MSelectionList()
        for vertId in neighboringVerts:
            sel.add(dag.fullPathName() + '.vtx[{0}]'.format(vertId))

        dag, neighboringVertices = sel.getComponent(0)

        return neighboringVertices, numNeighbors

    @classmethod
    def getVertexComponentFromId(cls, vertexId, meshName):
        sel = om.MSelectionList()
        sel.add('{0}.vtx[{1}]'.format(meshName, vertexId))
        dag, component = sel.getComponent(0)

        return component

    @classmethod
    def findUpstreamNodeOfType(cls, sourceMObject, nodeType):
        itDG = om.MItDependencyGraph(sourceMObject)
        itDG.resetTo(sourceMObject, nodeType, om.MItDependencyGraph.kUpstream, om.MItDependencyGraph.kDepthFirst,
                     om.MItDependencyGraph.kNodeLevel)

        if itDG.isDone():
            # No nodes upstream of that plug of the given type
            return None

        skinClusterMObject = None

        while not itDG.isDone():
            # return the first one we come across
            skinClusterMObject = itDG.currentNode()
            break

        return skinClusterMObject

    def doIt(self, args):
        # gather the values from args
        argParser = om.MArgParser(self.syntax(), args)

        self.vertexId = argParser.commandArgumentInt(0)
        self.strength = argParser.commandArgumentDouble(1)
        meshName = argParser.commandArgumentString(2)
        skinClusterName = argParser.commandArgumentString(3)

        sel = om.MSelectionList()
        sel.add(meshName)
        sel.add(skinClusterName)
        self.dagPath = sel.getDagPath(0)
        self.skinClusterMObject = sel.getDependNode(1)

        # get the dag path and component from the vertex id

        self.component = self.getVertexComponentFromId(self.vertexId, meshName)

        self.neighborComponents, self.numVertexNeighbors = self.getVertexNeighbors(self.dagPath, self.component)

        self.redoIt()

    def redoIt(self):
        # get the skin cluster MObject by going up the history

        fnSkinCluster = omAnim.MFnSkinCluster(self.skinClusterMObject)

        oldVertexWeight, numInfluences = fnSkinCluster.getWeights(self.dagPath, self.component)
        neighborVertexWeights, numInfluences = fnSkinCluster.getWeights(self.dagPath, self.neighborComponents)

        influenceIndices = om.MIntArray()
        newWeights = om.MDoubleArray()

        for i in xrange(numInfluences):
            # set the vertex weight to the average of its neighbor parts
            influenceIndices.append(i)
            newWeights.append(0.0)
            for j in xrange(i, len(neighborVertexWeights), numInfluences):
                # add to a rolling average. This will be normalized by default.
                # NOTE bmorgan: This formula comes from tf_smoothSkinWeight
                newWeights[i] += (((neighborVertexWeights[j] / self.numVertexNeighbors) * self.strength) +
                                  ((oldVertexWeight[i] / self.numVertexNeighbors) * (1 - self.strength)))

        fnSkinCluster.setWeights(self.dagPath, self.component, influenceIndices, newWeights)

        self.undoQueue.append((self.skinClusterMObject, oldVertexWeight, self.dagPath, influenceIndices, self.component))

    def undoIt(self):
        if self.undoQueue:
            fnSkinCluster = omAnim.MFnSkinCluster(self.undoQueue[-1][0])
            oldWeights = self.undoQueue[-1][1]
            meshDagPath = self.undoQueue[-1][2]
            influenceIndices = self.undoQueue[-1][3]
            component = self.undoQueue[-1][4]
            # when undoing, we have to set weights on every component
            fnSkinCluster.setWeights(meshDagPath, component, influenceIndices, oldWeights)

            self.undoQueue.pop(-1)


def cmdCreator():
    return bmSmoothSkinWeightsBrushCmd()


def initializePlugin(mObject):
    mPlugin = om.MFnPlugin(mObject)
    try:
        mPlugin.registerCommand(bmSmoothSkinWeightsBrushCmd.COMMAND_NAME, cmdCreator)
    except:
        sys.stderr.write('Failed to register command {}'.format(bmSmoothSkinWeightsBrushCmd.COMMAND_NAME))


def uninitializePlugin(mObject):
    mPlugin = om.MFnPlugin(mObject)
    try:
        mPlugin.deregisterCommand(bmSmoothSkinWeightsBrushCmd.COMMAND_NAME)
    except:
        sys.stderr.write('Failed to unregister command {}'.format(bmSmoothSkinWeightsBrushCmd.COMMAND_NAME))
