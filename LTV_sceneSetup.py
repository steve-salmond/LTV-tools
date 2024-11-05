import maya.cmds as cmds
import baseIO.getProj as getProj
import os

def makeGroup(groupName):
	grp = ''
	if cmds.objExists(groupName) == 0:
		grp = cmds.group( em=True, name=groupName )
	else:
		grp = groupName
	return grp

def referenceAssets(assetType,assetDict):
	
	selectedText = cmds.textScrollList('%sList'%assetType, q=True,selectIndexedItem=True)
	if selectedText:
		grp = makeGroup(assetType.upper())
		for i in selectedText:
			filePath = assetDict[i-1]['path']
			newAsset = cmds.file(filePath,r=True,loadReferenceDepth="all",returnNewNodes=True,namespace=assetDict[i-1]['name'].rsplit('_',1)[0])
			parentNames = []			
			for n in newAsset:
				if n[0] == '|':
					p = cmds.ls(n,long=True)[0].split('|')[1]
					if p:
						parentNames.append(p)
			
			parentNames = list(set(parentNames))
			for topNode in parentNames:
				cmds.parent(topNode,grp)

def doSetup():
	#set resolution
	cmds.setAttr("defaultResolution.width",1920)
	cmds.setAttr("defaultResolution.height",1080)
	cmds.currentUnit(time="pal")
	#set clipping plane on perspective camera
	cmds.setAttr("perspShape.nearClipPlane", 10)
	cmds.setAttr("perspShape.farClipPlane", 100000)


def addCamera():
	newCam = cmds.camera(n='RENDER_CAM')
	camGrp = makeGroup('CAMERAS')
	cmds.parent(newCam,camGrp)

def importCamRig():
	filepath="%s/scenes/_camera_rig_ref.ma"%getProj.getProject()
	cmds.file(filepath,i=True,type="mayaAscii",ignoreVersion=True,ra=True,mergeNamespacesOnClash=False)

def addSun():
	if cmds.objExists("SUN") == 0:
		newSun = cmds.directionalLight(n="SUN")
		newSunTransform = cmds.listRelatives(newSun,p=True,type="transform")
		lightGrp = makeGroup('LIGHTS')
		cmds.parent(newSunTransform,lightGrp)
	else:
		cmds.select("SUN",r=True)

def getParentFolder():
	#get parent folder
	projPath = getProj.getProject()
	scenePath = cmds.file(q=True,sn=True)
	parentFolder = projPath.rsplit('/',2)[0]
	pathLen = len(projPath.split('/'))
	remainingPath = scenePath.split('/',pathLen)[-1].rsplit('/',1)[0]
	return parentFolder,remainingPath

#list files of a type in a folder
def listFiles(path,filetype):
	#get project folder
	parentFolder,remainingPath = getParentFolder()
	#add relative path to folder
	pathName = '%s/%s'%(parentFolder,path)
	#make list for legitmate files
	fileNames = []
	#read folder
	if(os.path.isdir(pathName)):
		files = os.listdir(pathName)
		for f in files:
			#filter out filetypes
			if f.split('.')[-1] == filetype:
				#remove extention
				fileNames.append(f.split('.')[0])
		#remove duplicates
		fileNames = list(set(fileNames))
	fileNames.sort()
	return fileNames

def listFolders(path):
	#get project folder
	parentFolder,remainingPath = getParentFolder()
	#add relative path to folder
	pathName = '%s/%s'%(parentFolder,path)
	#make list for legitmate files
	fileNames = []
	#read folder
	if(os.path.isdir(pathName)):
		files = os.listdir(pathName)
		for f in files:
			#filter out filetypes
			if os.path.isdir('%s/%s'%(pathName,f)) and f[0] != '.':
				fileNames.append(f)
		#remove duplicates
		fileNames = list(set(fileNames))
	return fileNames

def findAssets():
	#create dictionary for assets
	assetDict = {}
	#list asset types
	assetFolders = listFolders('maya/scenes/models')
	#list assets within the types
	for assetType in assetFolders:
		typeDict = {assetType:[]}
		assetPath = 'maya/scenes/Models/%s'%assetType
		assets = listFiles(assetPath,'ma')
		dict = []
		for a in assets:
			aDict = {"name":  a,"path": 'scenes/models/%s/%s.ma'%(assetType,a)}
			dict.append(aDict)
		assetDict[assetType] = dict
		assets = listFiles(assetPath,'mb')
		for a in assets:
			aDict = {"name":  a,"path": 'scenes/models/%s/%s.mb'%(assetType,a)}
			dict.append(aDict)

	return assetDict

###		UI		###
def IoM_sceneSetup_window():
	#add ScriptNode to scene
	#scrptNode = cmds.createNode("script", n='IoMScriptNode',s=True)
	#if scrptNode:
	#	cmds.setAttr ("%s.scriptType"%scrptNode,1)
	#	cmds.setAttr ("%s.sourceType"%scrptNode,1)
	#	cmds.setAttr ("%s.after"%scrptNode,"import IoM_savePreset;IoM_savePreset.makePreset()",type="string")

	assetDict = findAssets()
	importForm = cmds.formLayout()

	colLayout = cmds.columnLayout('colLayout',cat=("both",0),adjustableColumn=True)
	setupLabel = cmds.text('setupLabel',label='Scene Setup',w=40,al='left',fn="boldLabelFont",h=20)
	setupButton = cmds.button('setupButton',l='Scene Setup',h=50,c='doSetup()')
	cmds.separator(height=20, style='in' )
	staticButtonForm = cmds.formLayout()
	camButton = cmds.button('camButton',l='Add Camera',annotation="Creates new camera",h=50,c='addCamera()')
	camRigButton = cmds.button('camRigButton',l='Add Camera Rig',annotation="import camera from scenes/_camera_rig_ref.ma",h=50,c='importCamRig()')
	#sunButton = cmds.button('sunButton',l='Add Sun',h=50,c='addSun()')
	cmds.formLayout(
		staticButtonForm,
		edit=True,
		attachForm=[
		(camButton,'left',0),
		(camRigButton,'right',0)
		],
		attachControl=[
		(camRigButton,'left',0,camButton)
		],
		attachPosition=[
		(camButton,'right',0,50)
		])

	

	cmds.setParent( '..' )
	
	assetsLabel = cmds.text('assetsLabel',label='Load assets',w=40,al='left',fn="boldLabelFont",h=20)
	for assetType in assetDict:
		cmds.frameLayout( label=assetType,collapsable=True,collapse=False)
		rowLayout = cmds.rowLayout(numberOfColumns=2,adj=1,cat=(2,"right",0))
		assetList = cmds.textScrollList('%sList'%assetType, h=80,allowMultiSelection=True)
		for asset in assetDict[assetType]:
			cmds.textScrollList('%sList'%assetType,e=True,append=asset['name'])
		cmds.textScrollList('%sList'%assetType,e=True,deselectAll=True)

		cmds.button('%sAddButton'%assetType,l="Add",h=80,w=50,c='referenceAssets(\'%s\',%s)'%(assetType,assetDict[assetType]))
		cmds.setParent( '..' )
		sep_assets = cmds.separator('%sSep'%assetType,height=20, style='in' )
		cmds.setParent( '..' )

	cmds.formLayout(
			importForm,
			edit=True,
			attachForm=[
				(colLayout,'left',10),
				(colLayout,'right',10),
				(colLayout,'top',10),
				(colLayout,'bottom',10)
				])
	

def IoM_setup():

	workspaceName = 'Scene Setup'
	if(cmds.workspaceControl(workspaceName, exists=True)):
		cmds.deleteUI(workspaceName)
	cmds.workspaceControl(workspaceName,initialHeight=100,initialWidth=300,uiScript = 'IoM_sceneSetup_window()')

#IoM_setup()

#import IoM_sceneSetup;from IoM_sceneSetup import *;IoM_setup()