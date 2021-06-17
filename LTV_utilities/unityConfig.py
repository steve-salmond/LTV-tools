import baseIO.getProj as getProj
import json
import LTV_utilities.fileWrangle as fileWrangle
import platform
import os
import maya.cmds as cmds

def preferedUnityVersion():
	projPath = getProj.getProject()
	settingsFile = '%sdata/projectSettings.json'%(projPath)
	with open(settingsFile) as json_data:
		data = json.load(json_data)
		json_data.close()
		return (data['unity']['preferedVersion'])

def getUnityProject():
	prefPath = fileWrangle.userPrefsPath()
	prefFile = '%s/LTV_prefs.json'%(prefPath)
	try:
		with open(prefFile) as json_data:
			data = json.load(json_data)
			json_data.close()
			unityProjectPath = data['unity']['project']
	except:
		print 'no existing pref file found'

	return unityProjectPath

def getUnityPath():

	prefPath = fileWrangle.userPrefsPath()
	prefFile = '%s/LTV_prefs.json'%(prefPath)
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

	jsonFileName  = '%s/LTV_prefs.json'%prefPath
	#write json to disk
	with open(jsonFileName, mode='w') as feedsjson:
		json.dump(userPrefsDict, feedsjson, indent=4, sort_keys=True)

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