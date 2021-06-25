import maya.cmds as cmds
import json

def readFilePrefs(attr):
	value = '' #value null string
	scenePath = cmds.file(q=True,sn=True) #get name of file
	seqFolder = scenePath.rsplit('/',2)[0] #find parent folder name
	pathName = "%s/seqPrefs.json"%seqFolder #add filename to path
	try:
		with open(pathName) as json_data: #open .json
			prefDict = json.load(json_data) #load json data into dictionary
			json_data.close() #close file
			value = prefDict[attr] #set value from .json file
	except:
		pass
	try:
		value = cmds.getAttr('LTV_filePrefs.%s'%(attr)) #get value from node and prioritise it over the .json file
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

	scenePath = cmds.file(q=True,sn=True)
	seqFolder = scenePath.rsplit('/',2)[0]
	pathName = "%s/seqPrefs.json"%seqFolder

	try:
		with open(pathName) as json_data:
			prefDict = json.load(json_data)
			json_data.close()
	except:
		prefDict = {"setName": ""}

	iomPrefNode = ''
	if cmds.objExists('LTV_filePrefs') == False:
		iomPrefNode = cmds.createNode('transform', name='LTV_filePrefs')
		cmds.setAttr('%s.visibility'%iomPrefNode,0)
		cmds.setAttr('%s.hiddenInOutliner'%iomPrefNode,1)
	else:
		iomPrefNode = 'LTV_filePrefs'
	setName = cmds.optionMenu('setSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'setName',setName)
	prefDict["setName"] = setName

	rows = cmds.columnLayout('boxLayout',ca=True,q=True) #list asset ui rows
	outfitDict = {}
	if rows:
		for i,r in enumerate(rows):
			checkBox = cmds.rowLayout(r,ca=True,q=True)[0] 
			dropdown = cmds.rowLayout(r,ca=True,q=True)[1] 
			if cmds.checkBox(checkBox,v=True, q=True):
				transform = cmds.checkBox(checkBox,annotation=True, q=True)
				name = cmds.checkBox(checkBox,l=True, q=True)
				outfitName = cmds.optionMenu(dropdown,q=True,v=True) #get outfit from menu
				outfitDict[name] = outfitName
				outfitDict[transform] = outfitName
	addAttrPlus(iomPrefNode,'Assets',json.dumps(outfitDict))
	prefDict["Assets"] = json.dumps(outfitDict)
	with open(pathName, mode='w') as feedsjson: #open the file for writing
		json.dump(prefDict, feedsjson, indent=4, sort_keys=True) #write dictionary out to file