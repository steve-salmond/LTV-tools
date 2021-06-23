import os
import baseIO.getProj as getProj
import maya.cmds as cmds
import platform

def getParentFolder():
	#get parent folder
	projPath = getProj.getProject()
	scenePath = cmds.file(q=True,sn=True)
	parentFolder = projPath.rsplit('/',2)[0]
	pathLen = len(projPath.split('/'))
	remainingPath = scenePath.split('/',pathLen)[-1].rsplit('/',1)[0]
	return parentFolder,remainingPath

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

def listAbsFolders(pathName):
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

def listAbsFiles(pathName,filetype):
	fileNames = [] #make list for legitmate files
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