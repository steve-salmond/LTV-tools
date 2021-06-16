import maya.cmds as cmds

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
	
	profileName = cmds.optionMenu('postProfileSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'profileName',profileName)
	setName = cmds.optionMenu('setSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'setName',setName)