import maya.cmds as cmds
import LTV_utilities.fileWrangle as fileWrangle
import os
import tempfile
from shutil import copyfile

def exportAsAlembic(abcFilename):

	#get file/folder path
	parentFolder,remainingPath = fileWrangle.getParentFolder()

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
		#cmds.file(abcExportPath.replace('.abc','_mat.fbx'),force=True,type='FBX export',es=True)

		returnString = "%s/%s_cache"%(remainingPath,abcFilename)
	
	return returnString

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
		exportObject = '%s|*CC3_Skeleton'%(obj)
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
	parentFolder,remainingPath = fileWrangle.getParentFolder()
	pathName = '%s/Unity/Assets/Resources/%s/%s'%(parentFolder,remainingPath,refFileName)
	#make folder if it doesn't exist
	if not os.path.exists(pathName.rsplit('/',1)[0]):
		os.makedirs(pathName.rsplit('/',1)[0])
	
	#load fbx presets from file
	#mel.eval("FBXLoadExportPresetFile -f \"%s/data/IoM_animExport.fbxexportpreset\";"%getProj.getProject())
	#export fbx
	#cmds.file(pathName,force=True,type='FBX export',relativeNamespace=ns,es=True)
	cmds.FBXExportBakeComplexAnimation("-v",True)
	cmds.FBXExportAnimationOnly("-v",True)
	cmds.FBXExportUseSceneName ("-v",True)
	cmds.FBXExport('-file', pathName,'-s')
	#restore the filename
	cmds.file(rename=filename)

	return obj,newName,remainingPath