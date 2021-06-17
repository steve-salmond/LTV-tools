import maya.cmds as cmds
import baseIO.sceneVar as sceneVar
import baseIO.getProj as getProj
import maya.mel as mel
import os
import baseIO.loadSave as IO
from shutil import copyfile
import json
import platform
import subprocess
import tempfile
import re
import LTV_utilities.fileWrangle as fileWrangle
import LTV_utilities.camera as cam
import LTV_utilities.formatExports as exp
import LTV_utilities.persistenceNode as persist
import LTV_utilities.unityConfig as unity
import LTV_utilities.unityConfig as bakeKeys

def selRef(asset):
	cmds.select(asset,r=True)

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
			#fullRefPath = cmds.referenceQuery( t, filename=True )
			#parentFolder = fullRefPath.split('/')[-2]
			#correctFile = 0
			#if parentFolder in assetFolders:
			correctFile = 1
			t=t[1:]
			publishedAssets.append({"transform":t,"publishedName":publishedName,"correctFile":correctFile})
		
	return publishedAssets

def browseToFolder():

	folder = cmds.fileDialog2(fileMode=3, dialogStyle=1)
	if folder:
		cmds.textFieldButtonGrp('unityPath',e=True,tx=folder[0])

	#format json
	userPrefsDict = {"unity": {"path":  folder[0]}}
	#make path
	prefPath = fileWrangle.userPrefsPath()
	#make folder
	if not os.path.exists(prefPath):
			os.makedirs(prefPath)

	jsonFileName  = '%s/IoM_prefs.json'%prefPath
	#write json to disk
	with open(jsonFileName, mode='w') as feedsjson:
		json.dump(userPrefsDict, feedsjson, indent=4, sort_keys=True)

	versions = unity.getUnityVersions(folder[0])
	menuItems = cmds.optionMenu('versionSelection', q=True, itemListLong=True)
	if menuItems:
		cmds.deleteUI(menuItems)
	for v in versions:
		cmds.menuItem(l=v)
	preferedVersion = unity.preferedUnityVersion()
	try:
		cmds.optionMenu('versionSelection',v=preferedVersion,e=True)
	except:
		pass


def disableMenu(checkbox,menu,textfield):
	checkValue = cmds.checkBox(checkbox,v=True,q=True)
	for obj in menu:
		cmds.optionMenu(obj,e=True,en=checkValue)
	for obj in textfield:
		cmds.textFieldButtonGrp(obj,e=True,en=checkValue)


def copyUnityScene():
	#get version of Unity from selection menu
	unityVersion = cmds.optionMenu('versionSelection',v=True,q=True)
	#check if checkBox is checked and a Unity version exists
	if cmds.checkBox('unityCheck',v=True,q=True) and len(unityVersion) > 0:
		#get file/folder path
		parentFolder,remainingPath = fileWrangle.getParentFolder()
		filename = cmds.file(q=True,sn=True,shn=True)
		#paths
		unityTemplateFile = '%s/Unity/Assets/Scenes/Templates/shotTemplate.unity'%(parentFolder)
		unitySceneFile = '%s/Unity/Assets/Scenes/%s/%s.unity'%(parentFolder,remainingPath,filename.split('.')[0])
		#make folder
		folder = unitySceneFile.rsplit('/',1)[0]
		if not os.path.exists(folder):
			os.makedirs(folder)
		
		#make Unity Scene File
		try:
			projectPath = "%s/Unity"%parentFolder
			scenePath = "Assets/Scenes/%s/%s.unity"%(remainingPath,filename.split('.')[0])
			shotName = "%s"%filename.split('.')[0]
			#get path to Unity from text field
			unityEditorPath = cmds.textFieldButtonGrp('unityPath',q=True,tx=True)
			if platform.system() == "Windows":
				subprocess.Popen('\"%s/%s/Editor/Unity.exe\" -quit -batchmode -projectPath \"%s\" -executeMethod BuildSceneBatch.PerformBuild -shotName \"%s\" -scenePath \"%s\" '%(unityEditorPath,unityVersion,projectPath,shotName,scenePath),shell=True)
			else:
				subprocess.Popen('%s/%s/Unity.app/Contents/MacOS/Unity -quit -batchmode -projectPath %s -executeMethod BuildSceneBatch.PerformBuild -shotName \"%s\" -scenePath \"%s\" '%(unityEditorPath,unityVersion,projectPath,shotName,scenePath),shell=True)
		except:
			print "Unable to populate Unity scene file"
			#copy blank Unity scene if auto population fails
			try:
				copyfile(unityTemplateFile, unitySceneFile)
			except:
				print "no Unity scene file created"
		





def prepFile(assetObject):
	#save scene
	persist.createFilePrefs()
	filename = cmds.file(save=True)

	parentFolder,remainingPath = fileWrangle.getParentFolder()

	#get start and end frame
	startFrame = sceneVar.getStartFrame()
	endFrame = sceneVar.getEndFrame()

	#add objects to selection if they are checked
	sel = []
	deformationSystems = []
	#start dictionary
	sceneDict = {"cameras": [],"characters": [],"extras": [],"sets": [],"lights": []}
	#checkBoxes = cmds.columnLayout('boxLayout',ca=True,q=True)
	rows = cmds.columnLayout('boxLayout',ca=True,q=True)
	if rows:
		for i,r in enumerate(rows):
			checkBox = cmds.rowLayout(r,ca=True,q=True)[0]
			if cmds.checkBox(checkBox,v=True, q=True):
				sel.append(assetObject[i])
				deformationSystems.append('%s|*:CC3_Skeleton'%assetObject[i])

		if sel:
			#bake keys
			#cmds.bakeResults(deformationSystems,simulation=True,t=(startFrame,endFrame),hierarchy='below',sampleBy=1,oversamplingRate=1,disableImplicitControl=True,preserveOutsideKeys=True,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,removeBakedAnimFromLayer=False,bakeOnOverrideLayer=False,minimizeRotation=True,controlPoints=False,shape=True)

			#export animation one object at a time
			for obj in sel:
				refPath = cmds.referenceQuery( obj,filename=True ) #get reference filename
				refNode = cmds.referenceQuery( obj,rfn=True ) #get name of reference node
				cmds.file(refPath,ir=True,referenceNode=refNode) #import reference to scene
				#remove namespace on skeleton
				cmds.select('%s|*:CC3_Skeleton'%obj,r=True) #select skeleton
				nodes = cmds.ls(sl=True,dag=True) #list chaild nodes
				for n in nodes:
					cmds.rename(n,n.split(":")[-1],ignoreShape=True) #rename child nodes
				#do the export
				print("obj = %s"%deformationSystems)
				obj,newName,remainingPath = exp.exportAnimation(obj)
				#make character dictionary
				try:
					#get REF filename
					publishName = cmds.getAttr('%s.publishName'%obj)
					#get asset type from parent folder
					assetType = os.path.split(os.path.dirname(refPath))[1]
					publishName = "%s/%s"%(assetType,publishName)
				except:
					#make a name if publishName attribute doesn't exist
					publishName = "%s/%s"%(remainingPath,newName.split('/')[-1])
				#format json
				displayName = re.split('\d+', newName)[-1][1:]
				charDict = {"name":  displayName,"model": publishName,"anim": "%s/%s"%(remainingPath,newName.split('/')[-1])}
				sceneDict["characters"].append(charDict)

	#add camera and post profile
	cameraName = cmds.optionMenu('cameraSelection',q=True,v=True)
	postProfile = cmds.optionMenu('postProfileSelection',q=True,v=True)
	print 'From selection %s'%postProfile
	setName = cmds.optionMenu('setSelection',q=True,v=True)
	if postProfile == 'From Set': #if no post profile is selected
		postProfile = '%s_PostProfile'%(setName) #set it as the set name
	if postProfile == 'No Profile':
		postProfile = '' #no profile should be used
	else:
		postProfile = 'Profiles/%s'%postProfile #post profile is from ui
	if postProfile:
		try: #copy post profile file
			postProfileTemplate = '%s/Unity/Assets/Resources/%s.asset'%(parentFolder,postProfile) #path to template post process file
			postProfileShot = '%s/Unity/Assets/Resources/Profiles/shotSpecific/%s.asset'%(parentFolder,filename.rsplit('/',1)[-1].split('.')[0]) #path to new post process file
			copyfile(postProfileTemplate, postProfileShot) #copy the file
		except:
			pass

	if cameraName:
		if len(cameraName) > 0:
			newCamera = cam.parentNewCamera(cameraName)[0]
			#bake keys
			cmds.bakeResults(newCamera,simulation=True,t=(startFrame,endFrame),hierarchy='below',sampleBy=1,oversamplingRate=1,disableImplicitControl=True,preserveOutsideKeys=True,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,removeBakedAnimFromLayer=False,bakeOnOverrideLayer=False,minimizeRotation=True,controlPoints=False,shape=True)

			obj,newName,remainingPath = exp.exportAnimation(newCamera)
			camDict = {"name":  "CAM","model": "%s/%s"%(remainingPath,newName.split('/')[-1]),"anim":"%s/%s"%(remainingPath,newName.split('/')[-1]),"profile":postProfile}
			sceneDict["cameras"].append(camDict)


	#export as alembic
	abcPath = exp.exportAsAlembic(filename.rsplit('/',1)[-1].split('.')[0])

	if len(abcPath) > 0:
		extraDict = {"name":  "extras","abc": abcPath,"material": '%s_mat'%abcPath}
		sceneDict["extras"].append(extraDict)

	#Add Sets to dictionary
	setName = cmds.optionMenu('setSelection',q=True,v=True)
	if setName and cmds.checkBox('setCheck',q=True,v=True) == True:
		if len(setName) > 0:
			setDict = {"name":  setName,"model": 'Sets/%s'%setName}
			sceneDict["sets"].append(setDict)
	#read set json file
	parentFolder,remainingPath = fileWrangle.getParentFolder()
	setProfiles = '%s/Unity/Assets/Resources/Sets/%s.json'%(parentFolder,setName)


	#write json file
	jsonFileName  = ('%s.json'%(filename.rsplit('/',1)[-1].split('.')[0]))
	
	pathName = '%s/Unity/Assets/Resources/json/%s'%(parentFolder,jsonFileName)
	try:
		os.mkdir('%s/Unity/Assets/Resources/json'%(parentFolder))
	except:
		pass
	with open(pathName, mode='w') as feedsjson:
		json.dump(sceneDict, feedsjson, indent=4, sort_keys=True)

	#revert to pre baked file
	#try:
	#	cmds.file(filename,open=True,force=True,iv=True)
	#except:
	#	pass

	#make new unity scene file
	copyUnityScene()

###		UI		###

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

def IoM_exportAnim_window():

	#find all published objects by searching for the 'publishName' attribute

	publishedAssets = findPublishedAssets()

	exportForm = cmds.formLayout()
	#Camera selection
	cameraLabel = cmds.text('cameraLabel',label='Camera',w=40,al='left')
	allCameras = cam.listAllCameras()
	cameraSelection = cmds.optionMenu('cameraSelection')
	for camera in allCameras:
		cmds.menuItem(l=camera)
	profiles = fileWrangle.listFiles('/Unity/Assets/Resources/Profiles','asset')
	profiles = ['From Set','No Profile'] + profiles
	postProfileSelection = cmds.optionMenu('postProfileSelection')
	for p in profiles:
		cmds.menuItem(l=p)
	preferedProfileName = persist.readFilePrefs('profileName')
	try:
		cmds.optionMenu('postProfileSelection',v=preferedProfileName,e=True)
	except:
		pass

	#Asset export
	sep_assets = cmds.separator("sep_assets",height=4, style='in' )
	assetsLabel = cmds.text('assetsLabel',label='Assets',w=40,al='left')
	publishedAsset = []
	#check for duplicates
	assetNames = []
	duplicates = False
	for asset in publishedAssets:
		assetNames.append(asset["transform"].split(':')[-1])
		assetNames.append(asset["publishedName"])
	if len(assetNames) != len(set(assetNames)):
		duplicates = True
	boxLayout = cmds.columnLayout('boxLayout',columnAttach=('both', 5), rowSpacing=10, columnWidth=350 )
	for asset in publishedAssets:
		cmds.rowLayout(numberOfColumns=2)
		publishedAsset.append(asset["transform"])
		if duplicates == False:
			cmds.checkBox(label=asset["publishedName"], annotation=asset["transform"],v=asset["correctFile"],onCommand='selRef(\"%s\")'%asset["transform"])
		else:
			cmds.checkBox(label=asset["publishedName"], annotation=asset["transform"],v=asset["correctFile"],onCommand='selRef(\"%s\")'%asset["transform"])

		if asset["correctFile"] == 0:
			#make button to show wrong REF
			errorButton = cmds.iconTextButton( style='iconOnly', image1='IoMError.svg', label='spotlight',h=20,w=20,annotation='Incorrect file used' )
			cmds.iconTextButton(errorButton,e=True,c='fixRef(\"%s\",\"%s\")'%(asset["transform"],errorButton))
		cmds.setParent( '..' )
	cmds.setParent( '..' )
	#Extras input
	sep2 = cmds.separator("sep2",height=4, style='in' )
	extrasLabel = cmds.text('extrasLabel',label='Extras',w=40,al='left')
	extrasList = cmds.textScrollList('extrasList',numberOfRows=8, allowMultiSelection=True,height=102)
	addButton = cmds.button('addButton',l='Add',h=50,w=50,c='addObjectsToScrollList()')
	removeButton = cmds.button('removeButton',l='Remove',h=50,w=50,c='removeObjectsFromScrollList()')
	#Unity export
	sep3 = cmds.separator("sep3",height=4, style='in' )
	versionLabel = cmds.text('versionLabel',label='Unity',w=40,al='left')
	versionSelection = cmds.optionMenu('versionSelection')
	myPath = unity.getUnityPath()
	versions = unity.getUnityVersions(myPath)
	for v in versions:
		cmds.menuItem(l=v)
	preferedVersion = unity.preferedUnityVersion()
	try:
		cmds.optionMenu('versionSelection',v=preferedVersion,e=True)
	except:
		pass
	unityCheck = cmds.checkBox('unityCheck',l="",annotation="Generate Unity scene file",v=True,cc='disableMenu(\'unityCheck\',[\'versionSelection\'],[\'unityPath\'])')
	unityPath = cmds.textFieldButtonGrp('unityPath',tx=myPath,buttonLabel='...',bc="browseToFolder()")
	sep4 = cmds.separator("sep4",height=4, style='in' )
	#Unity Set
	setLabel = cmds.text('setLabel',label='Set',w=40,al='left')
	setCheck = cmds.checkBox('setCheck',l="",annotation="Include Set",v=True,cc='disableMenu(\'setCheck\',[\'setSelection\'],[])')
	sets = fileWrangle.listFiles('/Unity/Assets/Resources/Sets','prefab')
	sets = sorted(sets) #sort alphabetaclly 
	setSelection = cmds.optionMenu('setSelection')
	for s in sets:
		cmds.menuItem(l=s)
	preferedSetName = persist.readFilePrefs('setName')
	try:
		cmds.optionMenu('setSelection',v=preferedSetName,e=True)
	except:
		pass
	#Main buttons
	Button1 = cmds.button('Button1',l='Publish',h=50,c='prepFile(%s)'%publishedAsset)
	Button2 = cmds.button('Button2',l='Close',h=50,c='cmds.deleteUI(\'Publish Animation\')') 
			 
	cmds.formLayout(
		exportForm,
		edit=True,
		attachForm=[
		(cameraLabel,'top',20),
		(cameraSelection,'top',15),
		(postProfileSelection,'top',15),
		(postProfileSelection,'right',10),
		(cameraLabel,'left',10),
		(sep_assets,'right',10),
		(sep_assets,'left',10),
		(assetsLabel,'left',10),
		(extrasLabel,'left',10),
		(extrasList,'left',10),
		(addButton,'right',10),
		(removeButton,'right',10),
		(sep2,'right',10),
		(sep2,'left',10),
		(sep3,'right',10),
		(sep3,'left',10),
		(versionLabel,'left',10),
		(versionSelection,'right',10),
		(unityPath,'right',10),
		(sep4,'right',10),
		(sep4,'left',10),
		(setLabel,'left',10),
		(setSelection,'right',10),
		(Button1,'bottom',0),
		(Button1,'left',0),
		(Button2,'bottom',0),
		(Button2,'right',0)
		],
		attachControl=[
		(cameraSelection,'left',40,cameraLabel),
		(postProfileSelection,'left',0,cameraSelection),
		(sep_assets,'top',60,cameraLabel),
		(assetsLabel,'top',20,sep_assets),
		(boxLayout,'top',20,sep_assets),
		(boxLayout,'left',40,cameraLabel),
		(sep2,'top',20,boxLayout),
		(extrasLabel,'top',40,boxLayout),
		(extrasList,'top',40,boxLayout),
		(extrasList,'right',10,addButton),
		(extrasList,'left',40,cameraLabel),
		(extrasList,'bottom',10,sep3),
		(addButton,'top',40,boxLayout),
		(removeButton,'top',2,addButton),
		(sep3,'bottom',60,sep4),
		(versionLabel,'top',20,sep4),
		(unityCheck,'left',40,versionLabel),
		(versionSelection,'top',50,sep4),
		(versionSelection,'left',60,versionLabel),
		(unityPath,'top',16,sep4),
		(unityPath,'left',60,versionLabel),
		(unityCheck,'top',20,sep4),
		(sep4,'bottom',100,Button1),
		(setLabel,'top',20,sep3),
		(setCheck,'top',20,sep3),
		(setCheck,'left',40,setLabel),
		(setSelection,'top',16,sep3),
		(setSelection,'left',60,setLabel),
		(Button2,'left',0,Button1)
		],
		attachPosition=[
		(Button1,'right',0,50),
		(cameraSelection,'right',0,60)
		])

	exportForm

def IoM_exportAnim():

	workspaceName = 'Publish Animation'
	if(cmds.workspaceControl(workspaceName, exists=True)):
		cmds.deleteUI(workspaceName)
	cmds.workspaceControl(workspaceName,initialHeight=100,initialWidth=300,uiScript = 'IoM_exportAnim_window()')

#IoM_exportAnim()
