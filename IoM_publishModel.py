import maya.cmds as cmds
import maya.mel as mel
import os, sys, time
import os.path
import baseIO.getProj as getProj
from shutil import copyfile
import platform
from LlamaIO import addAttribute

def cleanTexturePaths():
    fileNodes = cmds.ls(type='file')
    #project folder
    workspace = cmds.workspace( q=True, directory=True, rd=True)
    #texture folder
    textureFolder = cmds.workspace(fre='sourceImages')
    #full path
    fullPath=os.path.realpath('%s%s'%(workspace,textureFolder))
    
    for f in fileNodes:
        imgPath = cmds.getAttr('%s.fileTextureName'%f)
        parentFolder,remainingPath = getParentFolder()
        relativePath = '%s/%s'%(remainingPath,imgPath.split('/')[-1])
        #check if the file exists
        if os.path.isfile('%s/%s'%(fullPath,relativePath)):
            #change path    
            cmds.filePathEditor('%s.fileTextureName'%f,repath=relativePath.rsplit('/',1)[0],f=True)
        #check if file exists in wrong place
        elif os.path.isfile(imgPath):
            copyfile(imgPath, '%s/%s'%(fullPath,relativePath))
            #update path
            cmds.filePathEditor('%s.fileTextureName'%f,repath=relativePath.rsplit('/',1)[0],f=True)

def connectAttribute(objOut,attrOut,objIn,attrIn):
	#remove illegal characters
	attrIn = attrIn.split('|')[-1]
	attrIn = attrIn.split(':')[-1]
	attrIn = 'include_%s'%attrIn
	#delete attribute if it already exists
	if cmds.attributeQuery(attrIn,node=objIn,exists=True):
		cmds.deleteAttr('%s.%s'%(objIn,attrIn))
	#make new attribue
	cmds.addAttr(objIn,ln=attrIn,dataType='string')
	#connect attributes
	cmds.connectAttr('%s.message'%objOut, '%s.%s'%(objIn,attrIn),f=True)

def findGeoWithBlendShapes():
	#list of all geo affected by blendshapes
	blendGeo = []
	#find all blendshapes
	blendShapes = cmds.ls(type='blendShape')
	#loop through to find geo
	for b in blendShapes:
		connected = cmds.listConnections(b,destination=True,type='objectSet')
		for s in connected:
			members = cmds.sets( s, q=True )
			for m in members:
				blendGeo.append(m.split('.')[0])
	return blendGeo

###	 EXPORTS	 ###

def getParentFolder():
	#get parent folder
	projPath = getProj.getProject()
	scenePath = cmds.file(q=True,sn=True)
	parentFolder = projPath.rsplit('/',2)[0]
	pathLen = len(projPath.split('/'))+1
	remainingPath = scenePath.split('/',pathLen)[-1].rsplit('/',1)[0]
	print remainingPath
	return parentFolder,remainingPath

#export .fbx
def makeFbx(refName,obj):
	#unparent rig and geo
	geo = '|%s|Geometry'%obj
	bodyRig = '|%s|DeformationSystem'%obj

	#export fbx
	#define full file name
	refFileName  = refName+'.fbx'
	
	#get parent folder
	parentFolder,remainingPath = getParentFolder()
	
	#output name
	pathName = '%s/Unity/Assets/Resources/%s/%s'%(parentFolder,remainingPath.rsplit('/',1)[0],refFileName)
	if not os.path.exists(pathName.rsplit('/',1)[0]):
		os.makedirs(pathName.rsplit('/',1)[0])

	#make new selection
	cmds.select(geo,bodyRig,r=True)

	#export .fbx
	cmds.file(pathName,force=True,type='Fbx',pr=True,es=True)

	#reselect initial selection
	cmds.select(obj,r=True)

#export .ma
def makeRef(refName,publishString):
	#define full file name
	refFileName  = refName+'.ma'

	#add attribute to node for re-publishing
	addAttribute(publishString,'publishName',refName)

	
	#get parent folder
	scenePath = cmds.file(q=True,sn=True)
	parentFolder = scenePath.rsplit('/',2)[0]
	currentFolder = scenePath.rsplit('/',2)[1]
	
	#output name
	pathName = parentFolder+'/'+refFileName
	backupName = ""
	
	#if file exists, increment and back it up
	if os.path.isfile(pathName):
		#make backup folder
		backupFolder = '%s/%s/backup'%(parentFolder,currentFolder)
		if not os.path.exists(backupFolder):
			os.makedirs(backupFolder)
		count = 1
		backupExists = os.path.isfile('%s/%s%d'%(backupFolder,refFileName,count))
		while (backupExists == 1):
			count += 1
			backupExists = os.path.isfile('%s/%s%d'%(backupFolder,refFileName,count))
		backupName = '%s/%s%d'%(backupFolder,refFileName,count)
		copyfile(pathName, backupName)
	#export .mb REF
	if cmds.objExists('Sets'):
		cmds.select('Sets',add=True,ne=True)
	cmds.file(pathName,force=True,type='mayaAscii',pr=True,es=True)
	#log
	logOutput = []
	logOutput.append(pathName)
	logOutput.append(scenePath)
	logOutput.append(backupName)
	
	return logOutput


#update name and run
def PublishModelCheckText():
	
	#list objects
	sel = cmds.ls(sl=True)
	if len(sel) == 1:
		#get publish name from textfield
		publishName = cmds.textField('nameText',q=True,text=True)
		#get current selection so that it can be re-selected at the end
		tempSelect = cmds.ls(sl=True)
		
		#full path to scene
		scenePath = cmds.file(q=True,sn=True)
		#clean up texture paths
		#cleanTexturePaths()
		#binary
		makeRefLog = [0,0,0]
		cmds.select(tempSelect,r=True)
		#connect blendshape geo to rig
		bodyRig = '|%s|DeformationSystem'%tempSelect[0]
		blendshapes = findGeoWithBlendShapes()
		for b in blendshapes:
			connectAttribute(b,'message',bodyRig,b)
		makeRefLog = makeRef(publishName, sel[0])

		#fbx
		makeFbx(publishName, sel[0])
			
		#log
		writeLog(publishName, makeRefLog[0], makeRefLog[1], makeRefLog[2])
		
		#dialog
		CompleteDialog()

	#display errors
	elif len(sel) > 1:
		cmds.error('select only ONE object to publish')
	else:
		cmds.error('select an object to publish')
	
def publishModel():
	
	#list objects
	sel = cmds.ls(sl=True)
	if len(sel) == 1:
		#get publish name from textfield
		publishName = assumedPublishName()
		#get current selection so that it can be re-selected at the end
		tempSelect = cmds.ls(sl=True)
		
		#full path to scene
		scenePath = cmds.file(q=True,sn=True)

		#binary
		makeRefLog = [0,0,0]
		cmds.select(tempSelect,r=True)
		makeRefLog = makeRef(publishName, sel[0])

		#fbx
		makeFbx(publishName, sel[0])
			
		#log
		writeLog(publishName, makeRefLog[0], makeRefLog[1], makeRefLog[2])
		
		#dialog
		CompleteDialog(numberOfFiles)

	#display errors
	elif len(sel) > 1:
		cmds.error('select only ONE object to publish')
	else:
		cmds.error('select an object to publish')   


###	LOG	###

def writeLog(refFileName, pathName, scenePath, backupName):

	#log
	#get parent folder
	scenePath = cmds.file(q=True,sn=True)
	currentFolder = scenePath.rsplit('/',1)[0]
	#machine name 
	computer = platform.node()
	#Create A String Array With Test Data
	filePath = '%s/log/%s.mb.log'%(currentFolder,refFileName)
	if not os.path.exists('%s/log'%(currentFolder)):
		os.makedirs('%s/log'%(currentFolder))
	text_file = open(filePath, 'a')
	#Print Array To File
	log = '%s\nPublished to		%s\nPublished from	  %s\nBackup file	%s\nMachine			 %s\n\n'%(cmds.date(),pathName,scenePath,backupName,computer)
	text_file.write(log)
	#Close File
	text_file.close() 
		 
###	UI	###

#Complete Dialog
def CompleteDialog():

	#nice display message
	message = 'Exported'
	
	#create dialog
	response = cmds.confirmDialog(title='Completed!',
						  message=message,
						  button=['Okay','Close'],
						  defaultButton="Okay",
						  cancelButton="Close",
						  dismissString="Close")   
	if response == 'Close':

		cmds.deleteUI('Publish REF Window')


#set text field
def assumedPublishName():
	#check if publish name exists (object has been published before)
	sel = cmds.ls(sl=True)
	if sel and (cmds.attributeQuery('publishName', node=sel[0],exists=True)):
		publishName = cmds.getAttr(sel[0]+'.publishName')
	else:
		#guess publish name
		filename = cmds.file(q=True,sn=True,shn=True)
		splitName = filename.split('.')
		parts = splitName[0].split('_')
		publishName =  (parts[0] + "_REF")
	return publishName

def setTextField():
	publishName = assumedPublishName()
	cmds.textField('nameText',e=True,tx=publishName)

def IO_publishModel_window():
	#UI objects
	publishForm = cmds.formLayout()
	textLabel = cmds.text(label='Publish Name')
	nameText = cmds.textField('nameText',w=250)
	reloadButton = cmds.iconTextButton(style='iconOnly',image1='refresh.png',c='setText()')
	btn1 = cmds.button(l='Publish',h=50,c='PublishModelCheckText()')
	btn2 = cmds.button(l='Close',h=50,c='cmds.deleteUI(\'Publish REF Window\')')
	#UI layout
	cmds.formLayout(
		publishForm,
		edit=True,
		attachForm=[
		(textLabel,'top',15),
		(textLabel,'left',10),
		(reloadButton,'top',10),
		(reloadButton,'right',10),
		(nameText,'top',10),
		(btn1,'bottom',0),
		(btn1,'left',0),
		(btn2,'bottom',0),
		(btn2,'right',0)
		],
		attachControl=[
		(nameText,'left',10,textLabel),
		(nameText,'right',10,reloadButton),
		(btn2,'left',0,btn1)
		],
		attachPosition=[
		(btn1,'right',0,50)
		])
	setTextField()

def IO_publishModel(silent):
	if silent == 1:
		print 'silent mode'
		publishModel()
	else:
		workspaceName = 'Publish REF Window'
		if(cmds.workspaceControl(workspaceName, exists=True)):
			cmds.deleteUI(workspaceName)
		cmds.workspaceControl(workspaceName,initialHeight=100,initialWidth=300,uiScript = 'IO_publishModel_window()')

		

#IO_publishModel(0) 

#import IoM_publishModel
#IoM_publishModel.IO_publishModel(0)