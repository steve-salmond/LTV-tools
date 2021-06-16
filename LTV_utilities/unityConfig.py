import baseIO.getProj as getProj
import json
import LTV_utilities.fileWrangle as fileWrangle
import platform
import os

def preferedUnityVersion():
	projPath = getProj.getProject()
	settingsFile = '%sdata/projectSettings.json'%(projPath)
	with open(settingsFile) as json_data:
		data = json.load(json_data)
		json_data.close()
		return (data['unity']['preferedVersion'])

def getUnityPath():

	prefPath = fileWrangle.userPrefsPath()
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