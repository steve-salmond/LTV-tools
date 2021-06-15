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

def findPublishedAssets():
	publishedAssets = []
	allTransforms = cmds.ls(transforms=True,l=True)
	assetFolders = listFolders('maya/scenes/Models')
	for t in allTransforms:
		if cmds.attributeQuery( 'publishName', node=t, exists=True):
			fullRefPath = cmds.referenceQuery( t, filename=True )
			parentFolder = fullRefPath.split('/')[-2]
			correctFile = 0
			if parentFolder in assetFolders:
				correctFile = 1
			t=t[1:]
			publishedAssets.append({"transform":t,"correctFile":correctFile})
	return publishedAssets

def findDirectionalLights():
	lightTransforms = []
	lights = cmds.ls(type="directionalLight")
	for l in lights:
		p = cmds.listRelatives(l, p=True)[0]
		lightTransforms.append(p)
	return lightTransforms

def parentNewCamera(oldCamera):
	#find cameraShape
	camShape = cmds.listRelatives(oldCamera,type='camera')
	oldCamera = [oldCamera]
	oldCamera.append(camShape[0])
	#make new camera
	newCamera = cmds.camera(n='EXPORT_CAM');
	#copy transform attributes
	atttributes = ['rotatePivotX','rotatePivotY','rotatePivotZ','scalePivotX','scalePivotY','scalePivotZ']
	for a in atttributes:
		cmds.connectAttr('%s.%s'%(oldCamera[0],a),'%s.%s'%(newCamera[0],a))
	#constrain new camera to old camera
	cmds.parentConstraint(oldCamera[0],newCamera[0])
	#copy camera attributes
	atttributes = ['focalLength']
	for a in atttributes:
		cmds.connectAttr('%s.%s'%(oldCamera[1],a),'%s.%s'%(newCamera[1],a))
	#set extra attributes
	filmFit = cmds.getAttr('%s.filmFit'%oldCamera[1])
	cmds.setAttr('%s.filmFit'%newCamera[1],filmFit)
	cmds.setAttr('%s.nearClipPlane'%newCamera[1],10)
	cmds.setAttr('%s.farClipPlane'%newCamera[1],100000)
	#return new transform and shape as list
	return newCamera

def readFilePrefs(attr):
	value = ''
	try:
		value = cmds.getAttr('IoM_filePrefs.%s'%(attr))
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
	if cmds.objExists('IoM_filePrefs') == False:
		iomPrefNode = cmds.createNode('transform', name='IoM_filePrefs')
		cmds.setAttr('%s.visibility'%iomPrefNode,0)
		cmds.setAttr('%s.hiddenInOutliner'%iomPrefNode,1)
	else:
		iomPrefNode = 'IoM_filePrefs'
	
	profileName = cmds.optionMenu('postProfileSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'profileName',profileName)
	setName = cmds.optionMenu('setSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'setName',setName)
	rimName = cmds.optionMenu('rimSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'rimName',rimName)
	sunName = cmds.optionMenu('sunSelection',q=True,v=True)
	addAttrPlus(iomPrefNode,'sunName',sunName)

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
	return fileNames

def userPrefsPath():

	if platform.system() == "Windows":
		prefPath = os.path.expanduser('~/maya/prefs')
	else:
		prefPath = os.path.expanduser('~/Library/Preferences/Autodesk/Maya/prefs')
	return prefPath

def browseToFolder():

	folder = cmds.fileDialog2(fileMode=3, dialogStyle=1)
	if folder:
		cmds.textFieldButtonGrp('unityPath',e=True,tx=folder[0])

	#format json
	userPrefsDict = {"unity": {"path":  folder[0]}}
	#make path
	prefPath = userPrefsPath()
	#make folder
	if not os.path.exists(prefPath):
			os.makedirs(prefPath)

	jsonFileName  = '%s/IoM_prefs.json'%prefPath
	#write json to disk
	with open(jsonFileName, mode='w') as feedsjson:
		json.dump(userPrefsDict, feedsjson, indent=4, sort_keys=True)

	versions = getUnityVersions(folder[0])
	menuItems = cmds.optionMenu('versionSelection', q=True, itemListLong=True)
	if menuItems:
		cmds.deleteUI(menuItems)
	for v in versions:
		cmds.menuItem(l=v)
	preferedVersion = preferedUnityVersion()
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


def preferedUnityVersion():
	projPath = getProj.getProject()
	settingsFile = '%sdata/projectSettings.json'%(projPath)
	with open(settingsFile) as json_data:
		data = json.load(json_data)
		json_data.close()
		return (data['unity']['preferedVersion'])

def getUnityPath():

	prefPath = userPrefsPath()
	prefFile = '%s/IoM_prefs.json'%(prefPath)
	try:
		with open(prefFile) as json_data:
			data = json.load(json_data)
			json_data.close()
			unityEditorPath = data['unity']['path']
	except:
		print 'no existing pref file found, trying default Unity locations'

		if platform.system() == "Windows":
			unityEditorPath = "C:/Program Files/Unity/Hub/Editor"
		else:
			unityEditorPath = "/Applications/Unity/Hub/Editor"
	return unityEditorPath

def getUnityVersions(myPath):
	#list all versions of Unity on the system
	versions = []
	#filter out unnecessary folders 
	try:
		for f in os.listdir(myPath):
			if f[0] != '.' and os.path.isdir('%s/%s'%(myPath,f)):
				for e in os.listdir('%s/%s'%(myPath,f)):
					if e == 'Editor' or e == 'Unity.app':
						#build new list
						versions.append(f)
	except:
		pass
	return versions
		

def exportAsAlembic(abcFilename):

	#get file/folder path
	parentFolder,remainingPath = getParentFolder()

	#get workspace
	workspace = cmds.workspace( q=True, directory=True, rd=True)
	workspaceLen = len(workspace.split('/'))
	#get filename
	filename = cmds.file(q=True,sn=True)
	#get relative path (from scenes)
	relativePath = ''
	for dir in filename.split('/')[workspaceLen:-1]:
		relativePath += '%s/'%(dir)

	#string of objects to export
	exportString = ''
	returnString = ''
	sel = cmds.textScrollList('extrasList',q=True,allItems=True)
	if sel:
		for item in sel:
			exportString += ' -root %s'%(item)

		#get timeline
		startFrame = int(cmds.playbackOptions(q=True,minTime=True))
		endFrame = int(cmds.playbackOptions(q=True,maxTime=True))

		#set folder to export to  
		folderPath = '%s/Unity/Assets/Resources/%s'%(parentFolder,remainingPath)
		if not os.path.exists(folderPath):
			os.makedirs(folderPath)

		#check if plugin is already loaded
		if not cmds.pluginInfo('AbcImport',query=True,loaded=True):
			try:
				#load abcExport plugin
				cmds.loadPlugin( 'AbcImport' )
			except: 
				cmds.error('Could not load AbcImport plugin')

		#export .abc
		abcExportPath = '%s/%s_cache.abc'%(folderPath,abcFilename)
		abcTempPath = '%s/%s_cache.abc'%(tempfile.gettempdir().replace('\\','/'),abcFilename)
		command = '-frameRange %d %d -uvWrite -writeColorSets -writeFaceSets -writeVisibility -wholeFrameGeo -worldSpace -writeUVSets -dataFormat ogawa%s -file \"%s\"'%(startFrame,endFrame,exportString,abcTempPath)
		#load plugin
		if not cmds.pluginInfo('AbcExport',query=True,loaded=True):
			try:
				#load abcExport plugin
				cmds.loadPlugin( 'AbcExport' )
			except: cmds.error('Could not load AbcExport plugin')
		#write to disk
		cmds.AbcExport ( j=command )
		#copy file from temp folder to project
		copyfile(abcTempPath, abcExportPath)
		#export fbx for materials
		cmds.select(sel,r=True)
		print abcExportPath
		cmds.file(abcExportPath.replace('.abc','_mat.fbx'),force=True,type='FBX export',es=True)

		returnString = "%s/%s_cache"%(remainingPath,abcFilename)
	
	return returnString

def getParentFolder():
	#get parent folder
	projPath = getProj.getProject()
	scenePath = cmds.file(q=True,sn=True)
	parentFolder = projPath.rsplit('/',2)[0]
	pathLen = len(projPath.split('/'))
	remainingPath = scenePath.split('/',pathLen)[-1].rsplit('/',1)[0]
	return parentFolder,remainingPath

def copyUnityScene():
	#get version of Unity from selection menu
	unityVersion = cmds.optionMenu('versionSelection',v=True,q=True)
	#check if checkBox is checked and a Unity version exists
	if cmds.checkBox('unityCheck',v=True,q=True) and len(unityVersion) > 0:
		#get file/folder path
		parentFolder,remainingPath = getParentFolder()
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
		


#export fbx
def exportAnimation(obj):
	#rename file temporarily
	filename = cmds.file(q=True,sn=True)
	#objName = obj.split('|')[-1].split(':')[-1]
	objName = obj.split('|')[-1]
	objName = objName.replace(':','_')
	newName = '%s_%s'%(filename.rsplit('.',1)[0],objName)
	print 'new name = %s'%newName
	#move object to the root and redefine as itself if it's not already
	try:
		obj = cmds.parent(obj,w=True)[0]
	except:
		pass

	#select object to export
	try:
		exportObject = '%s|*:DeformationSystem'%(obj)
		cmds.select(exportObject,r=True)
	except:
		exportObject = obj
		cmds.select(exportObject,r=True)
	#define full file name
	if ':' in exportObject:
		ns = exportObject.split(':',1)[0]
		ns = ns.split('|')[-1]
		ns = ':%s'%ns
	else:
		ns = ':'
	refFileName  = ('%s.fbx'%(newName.rsplit('/',1)[-1].split('.')[0]))

	#output name
	parentFolder,remainingPath = getParentFolder()
	pathName = '%s/Unity/Assets/Resources/%s/%s'%(parentFolder,remainingPath,refFileName)
	#make folder if it doesn't exist
	if not os.path.exists(pathName.rsplit('/',1)[0]):
		os.makedirs(pathName.rsplit('/',1)[0])
	
	#load fbx presets from file
	mel.eval("FBXLoadExportPresetFile -f \"%s/data/IoM_animExport.fbxexportpreset\";"%getProj.getProject())
	#export fbx
	cmds.file(pathName,force=True,type='FBX export',relativeNamespace=ns,es=True)
	#restore the filename
	cmds.file(rename=filename)

	return obj,newName,remainingPath


def prepFile(assetObject):
	#save scene
	createFilePrefs()
	filename = cmds.file(save=True)

	parentFolder,remainingPath = getParentFolder()

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
				deformationSystems.append('%s|*:DeformationSystem'%assetObject[i])

		if sel:
			#bake keys
			cmds.bakeResults(deformationSystems,simulation=True,t=(startFrame,endFrame),hierarchy='below',sampleBy=1,oversamplingRate=1,disableImplicitControl=True,preserveOutsideKeys=True,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,removeBakedAnimFromLayer=False,bakeOnOverrideLayer=False,minimizeRotation=True,controlPoints=False,shape=True)

			#export animation one object at a time
			for obj in sel:
				#do the export
				obj,newName,remainingPath = exportAnimation(obj)
				#make character dictionary
				try:
					#get REF filename
					publishName = cmds.getAttr('%s.publishName'%obj)
					#get asset type from parent folder
					refPath = cmds.referenceQuery( obj,filename=True )
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

	rimProfile = cmds.optionMenu('rimSelection',q=True,v=True) #get selected rim profile from ui
	if rimProfile == 'No Profile':
		rimProfile = ''
	else:
		rimProfile = 'Profiles/rimlight/%s'%rimProfile
	if cameraName:
		if len(cameraName) > 0:
			newCamera = parentNewCamera(cameraName)[0]
			#bake keys
			cmds.bakeResults(newCamera,simulation=True,t=(startFrame,endFrame),hierarchy='below',sampleBy=1,oversamplingRate=1,disableImplicitControl=True,preserveOutsideKeys=True,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,removeBakedAnimFromLayer=False,bakeOnOverrideLayer=False,minimizeRotation=True,controlPoints=False,shape=True)

			obj,newName,remainingPath = exportAnimation(newCamera)
			camDict = {"name":  "CAM","model": "%s/%s"%(remainingPath,newName.split('/')[-1]),"anim":"%s/%s"%(remainingPath,newName.split('/')[-1]),"profile":postProfile,"rimProfile":rimProfile}
			sceneDict["cameras"].append(camDict)

	#add lights
	sunLight = cmds.optionMenu('sunSelection',q=True,v=True)
	if sunLight == 'Use Default':
		sunLight = ''
	else:
		x = cmds.getAttr('%s.rotateX'%sunLight)
		y = cmds.getAttr('%s.rotateY'%sunLight)
		z = cmds.getAttr('%s.rotateZ'%sunLight)
		camDict = {"angle": {"x":x,"y":y,"z":z}}
		sceneDict["lights"].append(camDict)

	#export as alembic
	abcPath = exportAsAlembic(filename.rsplit('/',1)[-1].split('.')[0])

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
	parentFolder,remainingPath = getParentFolder()
	setProfiles = '%s/Unity/Assets/Resources/Sets/%s.json'%(parentFolder,setName)
	#try:
	#	with open(setProfiles) as jsonSetData:
	#		setData = json.load(jsonSetData)
	#		jsonSetData.close()
	#		print setData["rimlight"]
	#		print setData["postProfile"]
	#except:
	#	pass


	#write json file
	jsonFileName  = ('%s.json'%(filename.rsplit('/',1)[-1].split('.')[0]))
	
	pathName = '%s/Unity/Assets/Resources/json/%s'%(parentFolder,jsonFileName)
	with open(pathName, mode='w') as feedsjson:
		json.dump(sceneDict, feedsjson, indent=4, sort_keys=True)

	



	
	#revert to pre baked file
	try:
		cmds.file(filename,open=True,force=True,iv=True)
	except:
		pass

	#make new unity scene file
	copyUnityScene()

#list cameras
def listAllCameras():
	cameraTransforms = []
	listAllCameras = cmds.listCameras(p=True)
	#remove 'persp' camera
	if 'persp' in listAllCameras: listAllCameras.remove('persp')
	for c in listAllCameras:
		if cmds.objectType(c) == "camera":
			cp = cmds.listRelatives(c,p=True)[0]
			cameraTransforms.append(cp)
		else:
			cameraTransforms.append(c)
	return cameraTransforms

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


###		UI		###
def IoM_exportAnim_window():

	#find all published objects by searching for the 'publishName' attribute

	publishedAssets = findPublishedAssets()

	exportForm = cmds.formLayout()
	#Camera selection
	cameraLabel = cmds.text('cameraLabel',label='Camera',w=40,al='left')
	allCameras = listAllCameras()
	cameraSelection = cmds.optionMenu('cameraSelection')
	for cam in allCameras:
		cmds.menuItem(l=cam)
	profiles = listFiles('/Unity/Assets/Resources/Profiles','asset')
	profiles = ['From Set','No Profile'] + profiles
	postProfileSelection = cmds.optionMenu('postProfileSelection')
	for p in profiles:
		cmds.menuItem(l=p)
	preferedProfileName = readFilePrefs('profileName')
	try:
		cmds.optionMenu('postProfileSelection',v=preferedProfileName,e=True)
	except:
		pass
	#Rim light 
	sep_rimLight = cmds.separator("sep_rimLight",height=4, style='in' )
	rimLabel = cmds.text('rimLabel',label='Rim Light',w=50,al='left')
	rimProfiles = listFiles('/Unity/Assets/Resources/Profiles/rimlight','json')
	rimProfiles = ['No Profile'] + rimProfiles
	rimSelection = cmds.optionMenu('rimSelection')
	for r in rimProfiles:
		cmds.menuItem(l=r)
	preferedRimProfileName = readFilePrefs('rimName')
	try:
		cmds.optionMenu('rimSelection',v=preferedRimProfileName,e=True)
	except:
		pass
	#Sun light 
	sep_sunLight = cmds.separator("sep_sunLight",height=4, style='in' )
	sunLabel = cmds.text('sunLabel',label='Sun Light',w=50,al='left')
	directionalLights = findDirectionalLights()
	directionalLights = ['Use Default'] + directionalLights
	sunSelection = cmds.optionMenu('sunSelection')
	for s in directionalLights:
		cmds.menuItem(l=s)
	preferedSunName = readFilePrefs('sunName')
	try:
		cmds.optionMenu('sunSelection',v=preferedSunName,e=True)
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
	if len(assetNames) != len(set(assetNames)):
		duplicates = True
	boxLayout = cmds.columnLayout('boxLayout',columnAttach=('both', 5), rowSpacing=10, columnWidth=350 )
	for asset in publishedAssets:
		cmds.rowLayout(numberOfColumns=2)
		publishedAsset.append(asset["transform"])
		if duplicates == False:
			cmds.checkBox(label=asset["transform"].split(':')[-1], annotation=asset["transform"],v=asset["correctFile"],onCommand='selRef(\"%s\")'%asset["transform"])
		else:
			cmds.checkBox(label=asset["transform"], annotation=asset["transform"],v=asset["correctFile"],onCommand='selRef(\"%s\")'%asset["transform"])

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
	myPath = getUnityPath()
	versions = getUnityVersions(myPath)
	for v in versions:
		cmds.menuItem(l=v)
	preferedVersion = preferedUnityVersion()
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
	sets = listFiles('/Unity/Assets/Resources/Sets','prefab')
	sets = sorted(sets) #sort alphabetaclly 
	setSelection = cmds.optionMenu('setSelection')
	for s in sets:
		cmds.menuItem(l=s)
	preferedSetName = readFilePrefs('setName')
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
		(sep_rimLight,'right',10),
		(sep_rimLight,'left',10),
		(sep_sunLight,'right',10),
		(sep_sunLight,'left',10),
		(sunLabel,'left',10),
		(sunSelection,'right',10),
		(rimLabel,'left',10),
		(rimSelection,'right',10),
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
		(sep_rimLight,'top',20,cameraLabel),
		(rimLabel,'top',20,sep_rimLight),
		(rimSelection,'top',15,sep_rimLight),
		(rimSelection,'left',30,rimLabel),
		(sep_sunLight,'top',60,sep_rimLight),
		(sunLabel,'top',20,sep_sunLight),
		(sunSelection,'top',15,sep_sunLight),
		(sunSelection,'left',30,sunLabel),
		(sep_assets,'top',60,sep_sunLight),
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
