import maya.cmds as cmds
import baseIO.sceneVar as sceneVar
import baseIO.getProj as getProj
import maya.mel as mel
import os
#import baseIO.loadSave as IO
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
import LTV_utilities.assetWrangle as assetWrangle
import LTV_utilities.uiAction as ui
		

def prepFile(assetObject):

	persist.createFilePrefs() #make a node to save ui settings in the scene
	filename = cmds.file(save=True) #save the scene file

	parentFolder,remainingPath = fileWrangle.getParentFolder() #get the path to parent folder
	startFrame = sceneVar.getStartFrame() #start frame
	endFrame = sceneVar.getEndFrame() #end frame

	### --- ASSETS --- ###

	#add objects to selection if they are checked
	sel = [] #list for checked assets
	deformationSystems = [] #list for asset rigs
	sceneDict = {"cameras": [],"characters": [],"extras": [],"sets": []} #dictionary for publish
	rows = cmds.columnLayout('boxLayout',ca=True,q=True) #list asset ui rows
	if rows:
		for i,r in enumerate(rows):
			checkBox = cmds.rowLayout(r,ca=True,q=True)[0] 
			if cmds.checkBox(checkBox,v=True, q=True):
				sel.append(assetObject[i]) #add asset if it's checked
				deformationSystems.append('%s|*:CC3_Skeleton'%assetObject[i]) #find rig of the asset and add it
		if sel: 
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
				sceneDict["characters"].append(charDict) #add to scene dictionary

	### --- CAMERA --- ###

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
			postProfileTemplate = '%s/Assets/Resources/%s.asset'%(unity.getUnityProject(),postProfile) #path to template post process file
			postProfileShot = '%s/Assets/Resources/Profiles/shotSpecific/%s.asset'%(unity.getUnityProject(),filename.rsplit('/',1)[-1].split('.')[0]) #path to new post process file
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
			sceneDict["cameras"].append(camDict) #add to scene dictionary


	### --- EXTRAS --- ###

	abcPath = exp.exportAsAlembic(filename.rsplit('/',1)[-1].split('.')[0]) #do alembic export 
	if len(abcPath) > 0: #check if anything is there
		extraDict = {"name":  "extras","abc": abcPath,"material": '%s_mat'%abcPath} #make dictionary for alembic
		sceneDict["extras"].append(extraDict) #add to scene dictionary

	### --- SET / ENVIRONMENT --- ###

	setName = cmds.optionMenu('setSelection',q=True,v=True)
	if setName and cmds.checkBox('setCheck',q=True,v=True) == True:
		if len(setName) > 0:
			setDict = {"name":  setName,"model": 'Sets/%s'%setName}
			sceneDict["sets"].append(setDict)
	#read set json file
	parentFolder,remainingPath = fileWrangle.getParentFolder()
	setProfiles = '%s/Assets/Resources/Sets/%s.json'%(unity.getUnityProject(),setName)


	#write json file
	jsonFileName  = ('%s.json'%(filename.rsplit('/',1)[-1].split('.')[0]))
	
	pathName = '%s/Assets/Resources/json/%s'%(unity.getUnityProject(),jsonFileName)
	try:
		os.mkdir('%s/Assets/Resources/json'%(unity.getUnityProject()))
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
	#get version of Unity from selection menu
	unityVersion = cmds.optionMenu('versionSelection',v=True,q=True)
	#check if checkBox is checked and a Unity version exists
	if cmds.checkBox('unityCheck',v=True,q=True) and len(unityVersion) > 0:
		unityEditorPath = cmds.textFieldButtonGrp('unityPath',q=True,tx=True)
		exp.copyUnityScene(unityVersion,unityEditorPath)

###		UI		###


def IoM_exportAnim_window():

	#find all published objects by searching for the 'publishName' attribute
	publishedAssets = assetWrangle.findPublishedAssets()

	exportForm = cmds.formLayout()
	#Camera selection
	cameraLabel = cmds.text('cameraLabel',label='Camera',w=40,al='left')
	allCameras = cam.listAllCameras()
	cameraSelection = cmds.optionMenu('cameraSelection')
	for camera in allCameras:
		cmds.menuItem(l=camera)
	profiles = fileWrangle.listFiles('%s/Assets/Resources/Profiles'%unity.getUnityProject(),'asset')
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
			cmds.checkBox(label=asset["publishedName"], annotation=asset["transform"],v=asset["correctFile"],onCommand='ui.selRef(\"%s\")'%asset["transform"])
		else:
			cmds.checkBox(label=asset["publishedName"], annotation=asset["transform"],v=asset["correctFile"],onCommand='ui.selRef(\"%s\")'%asset["transform"])

		if asset["correctFile"] == 0:
			#make button to show wrong REF
			errorButton = cmds.iconTextButton( style='iconOnly', image1='IoMError.svg', label='spotlight',h=20,w=20,annotation='Incorrect file used' )
			cmds.iconTextButton(errorButton,e=True,c='assetWrangle.fixRef(\"%s\",\"%s\")'%(asset["transform"],errorButton))
		cmds.setParent( '..' )
	cmds.setParent( '..' )
	#Extras input
	sep2 = cmds.separator("sep2",height=4, style='in' )
	extrasLabel = cmds.text('extrasLabel',label='Extras',w=40,al='left')
	extrasList = cmds.textScrollList('extrasList',numberOfRows=8, allowMultiSelection=True,height=102)
	addButton = cmds.button('addButton',l='Add',h=50,w=50,c='ui.addObjectsToScrollList()')
	removeButton = cmds.button('removeButton',l='Remove',h=50,w=50,c='ui.removeObjectsFromScrollList()')
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
	unityCheck = cmds.checkBox('unityCheck',l="",annotation="Generate Unity scene file",v=True,cc='ui.disableMenu(\'unityCheck\',[\'versionSelection\'],[\'unityPath\'])')
	unityPath = cmds.textFieldButtonGrp('unityPath',tx=myPath,buttonLabel='...',bc="unity.browseToFolder()")
	sep4 = cmds.separator("sep4",height=4, style='in' )
	#Unity Set
	setLabel = cmds.text('setLabel',label='Set',w=40,al='left')
	setCheck = cmds.checkBox('setCheck',l="",annotation="Include Set",v=True,cc='ui.disableMenu(\'setCheck\',[\'setSelection\'],[])')
	sets = fileWrangle.listFiles('%s/Assets/Resources/Sets'%unity.getUnityProject(),'prefab')
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
