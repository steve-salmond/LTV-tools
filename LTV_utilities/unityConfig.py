import baseIO.getProj as getProj
import json
import LTV_utilities.fileWrangle as fileWrangle
import platform
import os
import maya.cmds as cmds
import LTV_utilities.fileWrangle as fileWrangle

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

def getUnityPaths():
	currentProjects,activeProject = getUnityProject()
	pathFile = "%s/Assets/Resources/projectConfig.json"%currentProjects[activeProject]
	return pathFile

def updatePrefs(key,value):
	userPrefsDict = {"unity":{}} #format json
	keyDict = {"unity": {key:  value}} #format key
	prefPath = fileWrangle.userPrefsPath() #make path
	if not os.path.exists(prefPath):
		os.makedirs(prefPath) #make folder
	jsonFileName  = '%s/LTV_prefs.json'%prefPath #file name
	try:
		with open(jsonFileName) as json_data: #open the pref file if it exists
			print(jsonFileName)
			userPrefsDict = json.load(json_data) #update prefs dictionary from file
			json_data.close() #close pref file
	except:
		pass
	with open(jsonFileName, mode='w') as feedsjson: #open pref file for writing
		userPrefsDict["unity"].update(keyDict["unity"]) #update prefs from key dict
		json.dump(userPrefsDict, feedsjson, indent=4, sort_keys=True) #write new prefs to file

def browseToProject():
	folder = cmds.fileDialog2(fileMode=3, dialogStyle=1)
	currentProjects,activeProject = getUnityProject()
	if folder:
		currentProjects.append(folder[0])
		updatePrefs("projects",currentProjects) #update pref to file
		cmds.optionMenu('projSelection',e=True)
		cmds.menuItem( label=folder[0])
		cmds.optionMenu('projSelection',e=True,value=folder[0])
		menu_items = cmds.optionMenu('projSelection', query=True, itemListLong=True)
		last_index = len(menu_items)
		updatePrefs("active",last_index-1) #update pref to file


