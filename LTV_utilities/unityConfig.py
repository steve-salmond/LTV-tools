import baseIO.getProj as getProj
import json
import LTV_utilities.fileWrangle as fileWrangle
import platform
import os
import maya.cmds as cmds
import LTV_utilities.fileWrangle as fileWrangle

def preferedUnityVersion():
	currentProjects,activeProject = getUnityProject()
	settingsFile = "%s/ProjectSettings/ProjectVersion.txt"%currentProjects[activeProject]
	preferedVersion = "No prefered version set"
	try:
		file = open(settingsFile)
		line1 = file.readline()
		print (line1)
		preferedVersion = line1.split(":")[-1].strip()
		file.close()
	except:
		print("Project settings not found, make sure you have set your project")
	return preferedVersion

def getUnityProject():
	prefPath = fileWrangle.userPrefsPath()
	prefFile = '%s/LTV_prefs.json'%(prefPath)
	try:
		with open(prefFile) as json_data:
			data = json.load(json_data)
			json_data.close()
			unityProjectPath = data['unity']['projects']
			activeProject = data['unity']['active']
	except:
		print ('no existing pref file found')
		parentFolder,remainingPath = fileWrangle.getParentFolder()
		unityProjectPath = ["%s/Unity"%parentFolder]
		activeProject = 0

	return unityProjectPath,activeProject

def getUnityPath():
	prefPath = fileWrangle.userPrefsPath()
	prefFile = '%s/LTV_prefs.json'%(prefPath)
	try:
		with open(prefFile) as json_data:
			data = json.load(json_data)
			json_data.close()
			unityEditorPath = data['unity']['path']
	except:
		print ('no existing pref file found, trying default Unity locations')

		if platform.system() == "Windows":
			unityEditorPath = "C:/Program Files/Unity/Hub/Editor"
		else:
			unityEditorPath = "/Applications/Unity/Hub/Editor"
	return unityEditorPath

def getUnityPaths():
	currentProjects,activeProject = getUnityProject()
	pathFile = "%s/Assets/Resources/projectConfig.json"%currentProjects[activeProject]
	return pathFile

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

def updatePrefs(key,value):
	userPrefsDict = {"unity":{}} #format json
	keyDict = {"unity": {key:  value}} #format key
	prefPath = fileWrangle.userPrefsPath() #make path
	if not os.path.exists(prefPath):
		os.makedirs(prefPath) #make folder
	jsonFileName  = '%s/LTV_prefs.json'%prefPath #file name
	try:
		with open(jsonFileName) as json_data: #open the pref file if it exists
			userPrefsDict = json.load(json_data) #update prefs dictionary from file
			json_data.close() #close pref file
	except:
		pass
	with open(jsonFileName, mode='w') as feedsjson: #open pref file for writing
		userPrefsDict["unity"].update(keyDict["unity"]) #update prefs from key dict
		json.dump(userPrefsDict, feedsjson, indent=4, sort_keys=True) #write new prefs to file

def browseToFolder():
	folder = cmds.fileDialog2(fileMode=3, dialogStyle=1)
	if folder:
		cmds.textFieldButtonGrp('unityPath',e=True,tx=folder[0])
		
	updatePrefs("path",folder[0]) #update pref to file

	versions = getUnityVersions(folder[0])
	menuItems = cmds.optionMenu('versionSelection', q=True, itemListLong=True)
	if menuItems:
		cmds.deleteUI(menuItems)
	for v in versions:
		cmds.menuItem(l=v,parent='versionSelection')
	preferedVersion = preferedUnityVersion()
	try:
		cmds.optionMenu('versionSelection',v=preferedVersion,e=True)
	except:
		pass

#def browseToProject():
#	folder = cmds.fileDialog2(fileMode=3, dialogStyle=1)
#	if folder:
#		cmds.textFieldButtonGrp('projectPath',e=True,tx=folder[0])
		
#	updatePrefs("project",folder[0]) #update pref to file

def browseToProject():
	folder = cmds.fileDialog2(fileMode=3, dialogStyle=1)
	currentProjects,activeProject = getUnityProject()
	if folder:
		currentProjects.append(folder[0])
		updatePrefs("projects",currentProjects) #update pref to file
		cmds.optionMenu('projSelection',e=True)
		cmds.menuItem( label=folder[0])
		cmds.optionMenu('projSelection',e=True,value=folder[0])


