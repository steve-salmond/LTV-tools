import maya.cmds as cmds

def addObjectsToScrollList():
	#list selected objects
	sel = cmds.ls(sl=True)
	existing = cmds.textScrollList('extrasList',q=True,allItems=True)
	if existing:
		for text in existing:
			cmds.textScrollList('extrasList',e=True,removeItem=text)
		sel += existing
		sel = list(set(sel))
	
	cmds.textScrollList('extrasList',e=True,append=sel)
	
def removeObjectsFromScrollList():
	#list selected objects
	sel = cmds.textScrollList('extrasList',q=True,selectItem=True)
	for text in sel:
		cmds.textScrollList('extrasList',e=True,removeItem=text)

def selRef(asset):
	cmds.select(asset,r=True) 


def disableMenu(checkbox,menu,textfield):
	checkValue = cmds.checkBox(checkbox,v=True,q=True)
	for obj in menu:
		cmds.optionMenu(obj,e=True,en=checkValue)
	for obj in textfield:
		cmds.textFieldButtonGrp(obj,e=True,en=checkValue)