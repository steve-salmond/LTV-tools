import maya.cmds as cmds
import baseIO.sceneVar as sceneVar
import baseIO.getProj as getProj
import baseIO.loadSave as loadSave
import maya.mel as mel
import os
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

	blendGeo = [] #hold blendshapes
	blendShapes = cmds.ls(type='blendShape') #find all blendshapes
	cmds.bakeResults(blendShapes,simulation=True,t=(startFrame,endFrame),hierarchy='below',sampleBy=1,oversamplingRate=1,disableImplicitControl=True,preserveOutsideKeys=True,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,removeBakedAnimFromLayer=False,bakeOnOverrideLayer=False,minimizeRotation=True,controlPoints=False,shape=True)

	### --- ASSETS --- ###

	#add objects to selection if they are checked
	sel = [] #list for checked assets
	outfits = []
	#deformationSystems = [] #list for asset rigs
	sceneDict = {"cameras": [],"characters": [],"extras": [],"sets": []} #dictionary for publish
	rows = cmds.columnLayout('boxLayout',ca=True,q=True) #list asset ui rows
	if rows:
		for i,r in enumerate(rows):
			checkBox = cmds.rowLayout(r,ca=True,q=True)[0] 
			dropdown = cmds.rowLayout(r,ca=True,q=True)[1] 
			if cmds.checkBox(checkBox,v=True, q=True):
				sel.append(assetObject[i]) #add asset if it's checked
				#deformationSystems.append('%s|*:CC_Base_BoneRoot'%assetObject[i]) #find rig of the asset and add it
				outfitName = cmds.optionMenu(dropdown,q=True,v=True) #get outfit from menu
				outfits.append(outfitName) #add outfit if it's checked
		if sel: 
			#export animation one object at a time
			for i,obj in enumerate(sel):
				if cmds.referenceQuery( obj,inr=True ): #check if file is referenced
					refPath = cmds.referenceQuery( obj,filename=True ) #get reference filename
					refNode = cmds.referenceQuery( obj,rfn=True ) #get name of reference node
					cmds.file(refPath,ir=True,referenceNode=refNode) #import reference to scene
				nsLen = obj.split(":") #check if there is a namespace
				if len(nsLen) > 1:
					ns = obj.split(":")[0].split("|")[-1] #get namespace name
					grp = cmds.group(em=True,n="%s_grp"%ns) #make a group using the namespace
					cmds.parent(obj,grp) #parent the top asset node to the group
					cmds.namespace(moveNamespace=(ns,":"),force=True) #delete the namespace
					resolvedObjName = cmds.listRelatives(grp,c=True,f=True)[0] #find the asset node again
					cmds.rename(resolvedObjName,ns)
					resolvedObjName = cmds.listRelatives(grp,c=True,f=True)[0] #find the asset node again
				else:
					grp = cmds.listRelatives(obj,p=True)[0]
					resolvedObjName = obj

				skeleton = "%s|CC_Base_BoneRoot"%resolvedObjName #find the skeleton
				s = cmds.parent(skeleton,grp) #move the skeleton out of the asset node group
				childGeo = cmds.listRelatives('%s|Geometry'%resolvedObjName,c=True,f=True) #find the asset geometry 
				movedGeo = [] #hold the names of the geo after it's been moved
				for c in childGeo:
					geo = cmds.parent(c,grp) #move the geo out of the asset node group
					movedGeo.append(geo) #add new geo path to list

				obj,newName,remainingPath = exp.exportAnimation(resolvedObjName,False) #do the export
				#make character dictionary
				publishName = "unknown"
				try:
					publishName = cmds.getAttr('%s.publishName'%resolvedObjName) #get REF filename
				except:
					pass
				cmds.parent(s,resolvedObjName) #parent skeleton back into asset group
				for g in movedGeo: 
					cmds.parent(g,"%s|Geometry"%resolvedObjName) #parent geo back into asset group

				#format json
				displayName = publishName.split("_")[0]
				#displayName = re.split('\d+', newName)[-1][1:]
				
				charDict = {"name":  displayName,"anim": "%s/%s"%(remainingPath,newName.split('/')[-1]),"outfit": outfits[i]} 
				#charDict = {"name":  displayName,"model": publishName,"anim": "%s/%s"%(remainingPath,newName.split('/')[-1]),"outfit": outfitName} 
				sceneDict["characters"].append(charDict) #add to scene dictionary

	### --- CAMERA --- ###

	cameraName = cmds.optionMenu('cameraSelection',q=True,v=True) #get camera from menu
	if cameraName:
		if len(cameraName) > 0: #check if a camera has been selected
			newCamera = cam.parentNewCamera(cameraName)[0] #parent a new camera to work around grouping and scaling
			cmds.bakeResults(newCamera,simulation=True,t=(startFrame,endFrame),hierarchy='below',sampleBy=1,oversamplingRate=1,disableImplicitControl=True,preserveOutsideKeys=True,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,removeBakedAnimFromLayer=False,bakeOnOverrideLayer=False,minimizeRotation=True,controlPoints=False,shape=True) #bake camera keys
			obj,newName,remainingPath = exp.exportAnimation(newCamera,False) #export the camera animation
			if newCamera and isinstance(newCamera, list): #sometimes the camera returns a list
				newCamera = newCamera[0] #re-define the first object as string
			cmds.delete(newCamera) #delete the temp camera 
			camDict = {"name":  "CAM","model": "%s/%s"%(remainingPath,newName.split('/')[-1]),"anim":"%s/%s"%(remainingPath,newName.split('/')[-1])} #make a camera dictionary
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

	### --- WRITE JSON --- ###
	jsonFileName  = ('%s.json'%(filename.rsplit('/',1)[-1].split('.')[0])) #name json file based on scene file name
	pathName = '%s/Assets/Resources/json/%s'%(unity.getUnityProject(),jsonFileName) #find the correct path for the file to go
	try:
		os.mkdir('%s/Assets/Resources/json'%(unity.getUnityProject())) #make the folder if it doesn't exist
	except:
		pass
	with open(pathName, mode='w') as feedsjson: #open the file for writing
		json.dump(sceneDict, feedsjson, indent=4, sort_keys=True) #write dictionary out to file
	try:
		#cmds.file(filename,open=True,force=True,iv=True) #revert to pre baked file
		print("Debug")
	except:
		pass

	### --- UNITY --- ###

	unityVersion = cmds.optionMenu('versionSelection',v=True,q=True) #get version of Unity from selection menu
	if cmds.checkBox('unityCheck',v=True,q=True) and len(unityVersion) > 0: #check if checkBox is checked and a Unity version exists
		unityEditorPath = cmds.textFieldButtonGrp('unityPath',q=True,tx=True) #path to unity install
		exp.copyUnityScene(unityVersion,unityEditorPath) #build the unity scene

###		UI		###

def IoM_exportAnim_window():
	exportForm = cmds.formLayout() #start form
	#---------------------------------------------------------------------------------------------------------------------------------------------#
	#Camera selection
	#variables
	allCameras = cam.listAllCameras()
	#UI
	cameraLabel = cmds.text('cameraLabel',label='Camera',w=40,al='left') #camera label
	cameraSelection = cmds.optionMenu('cameraSelection') #make menu
	for camera in allCameras:
		cmds.menuItem(l=camera) #add cameras to menu
	#UI layout
	cmds.formLayout(
		exportForm,
		edit=True,
		attachForm=[
		(cameraLabel,'top',20),
		(cameraSelection,'top',15),
		(cameraSelection,'right',10),
		(cameraLabel,'left',10),
		(cameraSelection,'left',80)
		])
	#---------------------------------------------------------------------------------------------------------------------------------------------#
	#Asset export
	#variables
	publishedAssets = assetWrangle.findPublishedAssets() #find all published objects by searching for the 'publishName' attribute
	publishedAsset = [] #published asset null
	unityPath = unity.getUnityProject()
	#UI
	sep_assets = cmds.separator("sep_assets",height=4, style='in' ) #top of assets section
	assetsLabel = cmds.text('assetsLabel',label='Assets',w=40,al='left') #assets label
	boxLayout = cmds.columnLayout('boxLayout',columnAttach=('both', 5), rowSpacing=10, columnWidth=350 ) #new box layout
	for asset in publishedAssets: #for each asset
		cmds.rowLayout(numberOfColumns=2) #new row layout
		publishedAsset.append(asset["transform"]) #add transform to asset dictionary
		charName = cmds.getAttr("%s.publishName"%asset["transform"]).replace("_REF","") #get characters name 
		f = "%s/Assets/Characters/Json/%s.json"%(unity.getUnityProject(),charName) #path to character definition
		outfitNames = [] #hold outfit names
		try:
			charDict = loadSave.loadJSON(f) #load character json
			outfits = charDict["outfits"] #find outfits
			outfitNames = [li["name"] for li in outfits] #extract outfit names
		except:
			pass
		cmds.checkBox(label=asset["publishedName"].replace("_REF",""), annotation=asset["transform"],v=asset["correctFile"],onCommand='ui.selRef(\"%s\")'%asset["transform"]) #add checkbox
		outfitSelection = cmds.optionMenu() #make outfit menu
		for outfit in outfitNames:
			cmds.menuItem(l=outfit) #add outfit to menu
		if asset["correctFile"] == 0:
			errorButton = cmds.iconTextButton( style='iconOnly', image1='IoMError.svg', label='spotlight',h=20,w=20,annotation='Incorrect file used' ) #make error button if using the wrong reference file
			cmds.iconTextButton(errorButton,e=True,c='assetWrangle.fixRef(\"%s\",\"%s\")'%(asset["transform"],errorButton)) #add fix command to error button
		cmds.setParent( '..' )
	cmds.setParent( '..' )
	#UI layout
	cmds.formLayout(
		exportForm,
		edit=True,
		attachForm=[
		(sep_assets,'right',10),
		(sep_assets,'left',10),
		(sep_assets,'top',60),
		(assetsLabel,'left',10),
		(boxLayout,'left',80),
		],
		attachControl=[
		(assetsLabel,'top',20,sep_assets),
		(boxLayout,'top',20,sep_assets),
		])
	#---------------------------------------------------------------------------------------------------------------------------------------------#
	#Extras input
	#UI
	sep2 = cmds.separator("sep2",height=4, style='in' )
	extrasLabel = cmds.text('extrasLabel',label='Extras',w=40,al='left')
	extrasList = cmds.textScrollList('extrasList',numberOfRows=8, allowMultiSelection=True,height=102)
	addButton = cmds.button('addButton',l='Add',h=50,w=50,c='ui.addObjectsToScrollList()')
	removeButton = cmds.button('removeButton',l='Remove',h=50,w=50,c='ui.removeObjectsFromScrollList()')
	#UI layout
	cmds.formLayout(
		exportForm,
		edit=True,
		attachForm=[
		(extrasLabel,'left',10),
		(extrasList,'left',80),
		(addButton,'right',10),
		(removeButton,'right',10),
		(sep2,'right',10),
		(sep2,'left',10)
		],
		attachControl=[
		(sep2,'top',20,boxLayout),
		(extrasLabel,'top',40,boxLayout),
		(extrasList,'top',40,boxLayout),
		(extrasList,'right',10,addButton),
		(addButton,'top',40,boxLayout),
		(removeButton,'top',2,addButton)
		])
	#---------------------------------------------------------------------------------------------------------------------------------------------#
	#Environment
	#variables
	sets = fileWrangle.listAbsFiles('%s/Assets/Sets/Fbx'%unity.getUnityProject(),'fbx') #list all the environments in the Unity project
	sets = sorted(sets) #sort alphabetaclly #sort the environments
	#UI
	sep3 = cmds.separator("sep3",height=4, style='in' )
	setLabel = cmds.text('setLabel',label='Environment',w=70,al='left') #Environment label
	setCheck = cmds.checkBox('setCheck',l="",annotation="Include Set",v=True,cc='ui.disableMenu(\'setCheck\',[\'setSelection\'],[])') #Environment checkbox
	setSelection = cmds.optionMenu('setSelection') #make environment dropdown menu
	for s in sets:
		cmds.menuItem(l=s) #add environments to menu
	preferedSetName = persist.readFilePrefs('setName') #get set from previous save
	try:
		cmds.optionMenu('setSelection',v=preferedSetName,e=True) #set the set name if it's in the list
	except:
		pass
	#UI layout
	cmds.formLayout(
		exportForm,
		edit=True,
		attachForm=[
		(sep3,'right',10),
		(sep3,'left',10),
		(sep3,'bottom',200),
		(setLabel,'left',10),
		(setCheck,'left',80),
		(setSelection,'right',10)
		],
		attachControl=[
		(setLabel,'top',20,sep3),
		(setCheck,'top',20,sep3),
		(setSelection,'top',16,sep3),
		(setSelection,'left',10,setCheck)
		])
	#---------------------------------------------------------------------------------------------------------------------------------------------#
	#Unity export
	#variables
	myPath = unity.getUnityPath() #get path to unity install
	versions = unity.getUnityVersions(myPath) #list installed versions
	#UI
	sep4 = cmds.separator("sep4",height=4, style='in' ) #top of unity section
	versionLabel = cmds.text('versionLabel',label='Unity',w=40,al='left') #Unity label
	versionSelection = cmds.optionMenu('versionSelection') #version dropdown menu
	for v in versions:
		cmds.menuItem(l=v) #add versions to menu
	preferedVersion = unity.preferedUnityVersion()	#look for a prefered version of unity
	try:
		cmds.optionMenu('versionSelection',v=preferedVersion,e=True) #set the prefered version if it exists
	except:
		pass
	unityCheck = cmds.checkBox('unityCheck',l="",annotation="Generate Unity scene file",v=True,cc='ui.disableMenu(\'unityCheck\',[\'versionSelection\'],[\'unityPath\'])') #checkbox to make unity file
	unityPath = cmds.textFieldButtonGrp('unityPath',tx=myPath,buttonLabel='...',bc="unity.browseToFolder()") #textfield button to set path to unity
	#UI layout
	cmds.formLayout(
		exportForm,
		edit=True,
		attachForm=[
		(sep4,'right',10),
		(sep4,'left',10),
		(sep4,'bottom',140),
		(versionLabel,'left',10),
		(versionSelection,'right',10),
		(unityCheck,'left',80),
		(unityPath,'left',100),
		(unityPath,'right',10)
		],
		attachControl=[
		(versionLabel,'top',20,sep4),
		(versionSelection,'top',50,sep4),
		(versionSelection,'left',60,versionLabel),
		(unityPath,'top',16,sep4),
		
		(unityCheck,'top',20,sep4)
		])
	#---------------------------------------------------------------------------------------------------------------------------------------------#
	#Main buttons
	Button1 = cmds.button('Button1',l='Publish',h=50,c='prepFile(%s)'%publishedAsset)
	Button2 = cmds.button('Button2',l='Close',h=50,c='cmds.deleteUI(\'Publish Animation\')') 
	#UI layout
	cmds.formLayout(
		exportForm,
		edit=True,
		attachForm=[
		(Button1,'bottom',0),
		(Button1,'left',0),
		(Button2,'bottom',0),
		(Button2,'right',0)
		],
		attachControl=[
		(Button2,'left',0,Button1)
		],
		attachPosition=[
		(Button1,'right',0,50)
		])

	exportForm #finish the form

def IoM_exportAnim():

	workspaceName = 'Publish Animation'
	if(cmds.workspaceControl(workspaceName, exists=True)):
		cmds.deleteUI(workspaceName)
	cmds.workspaceControl(workspaceName,initialHeight=100,initialWidth=300,uiScript = 'IoM_exportAnim_window()')

#IoM_exportAnim()
