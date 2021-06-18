import maya.cmds as cmds
import os

def updateEnvFile(location):
	#set maya env variable 
	appPath = os.getenv('MAYA_APP_DIR') #path to documents/maya
	v=cmds.about(version=True) #get maya version
	envPath = "%s/%s/maya.env"%(appPath,v) #make path to .env

	file_object = open(envPath, 'r') #read file
	replaced_content = ""

	proj = cmds.workspace( q=True, directory=True, rd=True) #get project
	#scriptDir = '%sscripts'%proj #make script path
	scriptDir = location
	#update existing line
	existingPythonPath = "" #switch if path already exists
	for line in file_object:
	    line = line.strip() #remove whitespace
	    if "PYTHONPATH" in line and line[0] != "\\": 
	        existingPythonPath = line 
	        paths = line.split("=",1)[1] 
	        paths = paths.strip() #remove extra whitespace
	        pathList = paths.split(";") #get paths as list
	        pathList.append(scriptDir) #add new path to list
	        pathList = list(dict.fromkeys(pathList)) #remove duplicates from list
	        pathString = ';'.join(pathList) #rebuild list as string
	        line = "PYTHONPATH = %s"%pathString #build replacement line
	    replaced_content = replaced_content + line + "\n" #rebuild whole file
	#add new line
	if not existingPythonPath: #if there is not already a python path set
	    replaced_content = replaced_content + "PYTHONPATH = %s"%scriptDir #add line
	file_object.close() #close file

	#write new content to file
	file_object = open(envPath, 'w') #open file for writing
	file_object.write(replaced_content) #write new content
	file_object.close() #close file

	