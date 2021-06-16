import maya.cmds as cmds

def bakeKeys(skellyRoot):
	startframe = cmds.playbackOptions(q=True, min=True)
	endFrame = cmds.playbackOptions(q=True, max=True)

	cmds.bakeResults(skellyRoot,simulation=True,t=(startframe,endFrame),hierarchy="below",sampleBy=1, oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=True)
