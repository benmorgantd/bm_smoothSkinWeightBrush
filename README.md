![Brush Demo](https://i.imgur.com/j0fWZXY.gif)

# bm_smoothSkinWeightBrush

A skinning context for Autodesk Maya whose brush smooths all influences at once. Similar to Brave Rabbit's smooth skin weight brush, and very similar to the ancient _tfSmoothSkinWeight_ brush from turbosquid. 

The goal for this project was to figure out how to get a custom paint tool working and to document that online for others.

The plug-in for this brush is written in Python, so the brush isn't great at very high vertex and influence densities. I use this mainly on game-resolution meshes.

Tested in Maya 2020 (uses OpenMaya API 2.0), so this *might* work in 2016+ but it hasn't been tested enough to be sure. 

> Because it runs off of a command, the action of this brush is safely undoable 

## How to Install (Easy Mode)
1. Download the zip for this repository
2. Put the contents of the plug-ins folder in your Maya plug-ins folder
3. Put the contents of the scripts folder in your Maya scripts folder
4. Open Maya
5. Open the Plug-in Manager and load `bm_SmoothSkinWeightBrushCmd`. Also set it to AutoLoad so you don't have to do this each time. 

## How to Install (Slightly Less Easy Mode)
1. Download the zip for this repository
2. In your Maya installation's Maya.env file, append the path to ...bm_smoothSkinWeightsBrush/scripts and /plig-ins to the MAYA_SCRIPT_LOC and MAYA_PLUG_IN_PATH variables respectively.
* See the [Autodesk Docs on Maya.env](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2020/ENU/Maya-EnvVar/files/GUID-8EFB1AC1-ED7D-4099-9EEE-624097872C04-htm.html) for more information
3. Open Maya
4. Load `bm_SmoothSkinWeightsBrushCmd` in the Plug-in Manager. Set it to Auto Load

* This technique allows you to keep this repo in a folder location apart from your normal maya install loc, which can make working with git a little easier. 

## Running the tool
#### Mel
`source bm_smoothSkinWeightBrush;`


#### Python
```
import maya.mel
maya.mel.eval("source bm_smoothSkinWeightBrush;")
```


## Using the brush
0. I usually find it useful to put my rig in am extreme pose while smoothing weights.
1. Select the transform, shape, or vertex of a skinned mesh
2. Paint the vertices you want to smooth
3. Press q to exit the tool context, or any other way you'd normally exit the Paint Skin Weights tool

* Adjusting the brush's opacity and profile adjusts the intensity of the smooth effect.
* You can undo a stroke with ctrl+z
* The actual brush command you use (replace, add, scale, etc) has no effect
* The resulting weights from the tool will be normalized 
* The resulting weights from the tool will likely be > 4 influences per vertex if that matters for you

## Technical Documentation

### Plug-in Documentation
#### High Level
* The plug-in command, at a basic level, is designed to set the weight of a single vertex to the average weight of its neighbors. 
* The command runs 2 getWeights calls: one for a single vertex and another for its neighbors
* The command runs 1 setWeights call on a single vertex
* The command's args include: `shapeName, skinClusterName, vertexId, strength`
* The command stores the previous value of the weight in memory so that the action can be undone. 


