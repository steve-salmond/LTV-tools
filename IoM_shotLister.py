import maya.cmds as cmds
import os
import baseIO.getProj as getProj

def listAllShots():
	projPath = getProj.getProject()
	pathName = '%s../Unity/Assets/Resources/json'%projPath
	print pathName
	
	files = os.listdir(pathName)
	
	shDict = {}
	EPs = []
	SEQs = []
	SHs = []
	for f in files:
		if f.split('.')[-1] == 'json':
			print f
			
			asList = f.split('_')
			EP = [s for s in asList if "EP" in s]
			SEQ = [s for s in asList if "SEQ" in s]
			SH = [s for s in asList if "SH" in s]
			V = [s for s in asList if "v" in s]
			
			if EP:
				if EP[0] not in shDict:
					shDict[EP[0]] = {}
				if SEQ[0] not in shDict[EP[0]]:
					shDict[EP[0]][SEQ[0]] = {}
				if SH[0] not in shDict[EP[0]][SEQ[0]]:
					shDict[EP[0]][SEQ[0]][SH[0]] = {}
				shDict[EP[0]][SEQ[0]][SH[0]] = f
		
	return shDict

def clearOptionMenu(menuName):
	menuItems = cmds.optionMenu(menuName, q=True, itemListLong=True)
	if menuItems:
		cmds.deleteUI(menuItems)

def setSeq(allShots):
	currentEp = cmds.optionMenu('EPMenu',q=True,v=True)	
	cmds.optionMenu('SEQMenu',e=True)
	clearOptionMenu('SEQMenu')
	for key in allShots[currentEp]:
		cmds.menuItem(l=key)

def setSh(allShots):
	print "set shot"
	currentEp = cmds.optionMenu('EPMenu',q=True,v=True)
	currentSeq = cmds.optionMenu('SEQMenu',q=True,v=True)	
	cmds.optionMenu('SHMenu',e=True)
	clearOptionMenu('SHMenu')
	for key in allShots[currentEp][currentSeq]:
		cmds.menuItem(l=key)

allShots = listAllShots()
print allShots
cmds.window()
cmds.rowLayout( numberOfColumns=3 )
EPMenu = cmds.optionMenu('EPMenu')
for key in allShots:
	cmds.menuItem(l=key)
	
SEQMenu = cmds.optionMenu('SEQMenu',cc='setSh(%s)'%allShots)
setSeq(allShots)


SHMenu = cmds.optionMenu('SHMenu')
setSh(allShots)

cmds.showWindow()











