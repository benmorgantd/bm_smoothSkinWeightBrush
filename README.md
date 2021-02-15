# bm_smoothSkinWeightBrush
A skinning context for Autodesk Maya whose brush smooths all influences at once. 

Tested in Maya 2020 (uses OpenMaya API 2.0)

## How to Install (Easy Mode)
1. Download the zip for this repository
2. Put the contents of the plug-ins folder in your Maya plug-ins folder
3. Put the contents of the scripts folder in your Maya scripts folder
4. Open Maya
5. Open the Plug-in Manager and load bm_SmoothSkinWeightBrushCmd. Also set it to AutoLoad so you don't have to do this each time. 

## Running the tool
#### Mel
  *source bm_smoothSkinWeightBrush;*
*

#### Python
  *import maya.mel*
  *maya.mel.eval("source bm_smoothSkinWeightBrush;")*
