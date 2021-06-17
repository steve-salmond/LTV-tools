import maya.cmds as cmds
import os
import baseIO.getProj as getProj
import LTV_utilities.fileWrangle as fileWrangle


def fixRef(asset,errorButton):

	#get full path to incorrectly referenced file
	fullRefPath = cmds.referenceQuery( asset, filename=True )

	publishName = ''
	#try and get name from top transform publish attribute
	if cmds.attributeQuery('publishName',n=asset,exists=True):
		publishName = cmds.getAttr('%s.publishName'%asset)
	else:
		#try and get the name from the start of the incorrect filename
		publishName = '%s_REF'%fullRefPath.split('/')[-1].split('_')[0]
	
	#find ref node
	refNode = cmds.referenceQuery( asset, referenceNode=True )
	parentFolder = 'scenes/Models/%s'%fullRefPath.split('/')[-3]
	projPath = getProj.getProject()
	#check assumed path exists
	checkExistsPath = '%s%s/%s.ma'%(projPath,parentFolder,publishName)
	newPath = '%s/%s.ma'%(parentFolder,publishName)
	if os.path.isfile(checkExistsPath):
		#set new path 
		cmds.file(newPath, loadReference = refNode)
		#hide button
		cmds.iconTextButton(errorButton,e=True,vis=False)

def findPublishedAssets():
	publishedAssets = []
	allTransforms = cmds.ls(transforms=True,l=True)
	assetFolders = fileWrangle.listFolders('maya/scenes/Models')
	for t in allTransforms:
		if cmds.attributeQuery( 'publishName', node=t, exists=True):
			publishedName = cmds.getAttr("%s.publishName"%t)
			fullRefPath = cmds.referenceQuery( t, filename=True )
			parentFolder = fullRefPath.split('/')[-2]
			correctFile = 0
			if parentFolder in assetFolders:
				correctFile = 1
			t=t[1:]
			publishedAssets.append({"transform":t,"publishedName":publishedName,"correctFile":correctFile})
		
	return publishedAssets