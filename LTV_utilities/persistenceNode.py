import maya.cmds as cmds
import json

def readFilePrefs(attr):
	value = ''
	try:
		value = cmds.getAttr('LTV_filePrefs.%s'%(attr))
	except:
		pass
	return value

def addAttrPlus(obj,attr,v):
	value = ''
	if v:
		value = v
	attrExists = cmds.attributeQuery(attr, node=obj, exists=True)
	if attrExists == False:
		cmds.addAttr(obj,ln=attr,dt='string')
	cmds.setAttr('%s.%s'%(obj,attr),value,type='string')

def createFilePrefs():
	iomPrefNode = ''
	if cmds.objExists('LTV_filePrefs') == False:
		iomPrefNode = cmds.createNode('transform', name='LTV_filePrefs')
		cmds.setAttr('%s.visibility'%iomPrefNode,0)
		cmds.setAttr('%s.hiddenInOutliner'%iomPrefNode,1)
	else:
		iomPrefNode = 'LTV_filePrefs'
	
	#profileName = cmds.optionMenu('postProfileSelection',q=True,v=True)
	#addAttrPlus(iomPrefNode,'profileName',profileName)
	setName = cmds.optionMenu('setSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'setName',setName)

	rows = cmds.columnLayout('boxLayout',ca=True,q=True) #list asset ui rows
	outfitDict = {}
	if rows:
		for i,r in enumerate(rows):
			checkBox = cmds.rowLayout(r,ca=True,q=True)[0] 
			dropdown = cmds.rowLayout(r,ca=True,q=True)[1] 
			if cmds.checkBox(checkBox,v=True, q=True):
				name = cmds.checkBox(checkBox,l=True, q=True)
				outfitName = cmds.optionMenu(dropdown,q=True,v=True) #get outfit from menu
				outfitDict[name] = outfitName


	addAttrPlus(iomPrefNode,'Assets',json.dumps(outfitDict))