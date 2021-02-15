import sys

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omAnim


def maya_useNewAPI():
    pass


class bmSmoothSkinWeightsBrushCmd(om.MPxCommand):
    COMMAND_NAME = 'bmSmoothSkinWeightsBrushCmd'
    # stores an array of tuples that has the data necessary to undo setting weights
    undoQueue = []
    # the dag path of the mesh's shape node
    shapeDag = om.MDagPath()
    # the mobject for our mesh's skin cluster
    skinClusterMObject = om.MObject()
    # the mobject that points to the given vertex
    component = om.MObject()
    # the mobject that points to the given vertex's neighbors
    neighborComponents = om.MObject()
    # the given vertex id to smooth
    vertexId = None
    # the strength at which to smooth, where 0 does nothing.
    strength = 1.0
    # the number of neighbors this vertex has. Needed for the average function.
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
        self.shapeDag = sel.getDagPath(0)
        self.skinClusterMObject = sel.getDependNode(1)

        # create a single index component mfn and assign our given vertex id to it
        self.component = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(self.component).addElement(self.vertexId)

        # get the nighbors of this vertex
        itVert = om.MItMeshVertex(self.shapeDag, self.component)
        neighborVertList = itVert.getConnectedVertices()
        # TODO: with this iterator, we could also query if this vertex is a border vertex.
        # We could skip the redo function altogether if we wanted to pin border vertices

        self.numVertexNeighbors = len(neighborVertList)

        # Create a single indexed component mfn and assign the neighbor component array to it.
        self.neighborComponents = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(self.neighborComponents).addElements(neighborVertList)

        self.redoIt()

    def redoIt(self):
        fnSkinCluster = omAnim.MFnSkinCluster(self.skinClusterMObject)

        # get the weights for our single vertex plus its neighbors
        oldVertexWeight, numInfluences = fnSkinCluster.getWeights(self.shapeDag, self.component)
        neighborVertexWeights, numInfluences = fnSkinCluster.getWeights(self.shapeDag, self.neighborComponents)
        neighborVertexWeightLength = self.numVertexNeighbors * numInfluences

        influenceIndices = om.MIntArray()
        newWeights = om.MDoubleArray()

        # set the vertex weight to the average of its neighbor parts
        for i in xrange(numInfluences):
            # taking advantage of this loop to create our influence indices array
            influenceIndices.append(i)
            # weights start at 0 so that we can add weight values to it
            newWeights.append(0.0)
            for j in xrange(i, neighborVertexWeightLength, numInfluences):
                # add to a rolling average. This will be normalized by default.
                # NOTE bmorgan: This formula comes from tf_smoothSkinWeight
                newWeights[i] += (((neighborVertexWeights[j] / self.numVertexNeighbors) * self.strength) +
                                  ((oldVertexWeight[i] / self.numVertexNeighbors) * (1 - self.strength)))

        # set the skin cluster weight for just that single component
        fnSkinCluster.setWeights(self.shapeDag, self.component, influenceIndices, newWeights)

        # add the previous weight value to our undo queue
        self.undoQueue.append((self.skinClusterMObject, oldVertexWeight, self.shapeDag, influenceIndices, self.component))

    def undoIt(self):
        if self.undoQueue:
            fnSkinCluster = omAnim.MFnSkinCluster(self.undoQueue[-1][0])
            oldWeight = self.undoQueue[-1][1]
            shapeDag = self.undoQueue[-1][2]
            influenceIndices = self.undoQueue[-1][3]
            component = self.undoQueue[-1][4]
            # when undoing, we're also only setting the weight on that single vertex
            fnSkinCluster.setWeights(shapeDag, component, influenceIndices, oldWeight)

            # after we've set weights, remove that data from the undo queue
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
