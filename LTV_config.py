import maya.cmds as cmds
import LTV_utilities.unityConfig as unity

### --- UI --- ###

def LTV_config_window():
	configForm = cmds.formLayout() #start the form
	#Unity Binary location
	#variables
	preferedVersion = unity.preferedUnityVersion() #look for prefered unity version in project config
	unityBinaryPath = unity.getUnityPath() #try find existing config, uses default install path if non found
	versions = unity.getUnityVersions(unityBinaryPath) #look for installed unity versions
	#UI
	binaryLabel = cmds.text('binaryLabel',label='Binary path',w=100,al='left') #binary path label
	versionSelection = cmds.optionMenu('versionSelection') #version selection dropdown menu
	for v in versions:
		cmds.menuItem(l=v) #add version to dropdown menu
	try:
		cmds.optionMenu('versionSelection',v=preferedVersion,e=True) #set menu to prefered version if it exists
	except:
		pass
	unityPath = cmds.textFieldButtonGrp('unityPath',tx=unityBinaryPath,buttonLabel='...',bc="unity.browseToFolder()") #binary textfield button
	# UI layout
	cmds.formLayout(
		configForm,
		edit=True,
		attachForm=[
		(binaryLabel,'left',10),
		(binaryLabel,'top',20),
		(versionSelection,'top',50),
		(versionSelection,'right',10),
		(unityPath,'top',16),
		(unityPath,'right',10)
		],
		attachControl=[
		(versionSelection,'left',10,binaryLabel),
		(unityPath,'left',10,binaryLabel)
		]
		)
	#Unity Project location
	#Variables
	unityProject = unity.getUnityProject() #try find existing config, uses path relative to maya project if non found
	#UI
	sep_proj = cmds.separator("sep_proj",height=4, style='in' ) #top separator & project config anchor
	projectLabel = cmds.text('projectLabel',label='Project path',w=100,al='left') #project label
	projectPath = cmds.textFieldButtonGrp('projectPath',tx=unityProject,buttonLabel='...',bc="unity.browseToProject()") #project textfield button
	# UI layout
	cmds.formLayout(
		configForm,
		edit=True,
		attachForm=[
		(sep_proj,'top',90),
		(sep_proj,'right',10),
		(sep_proj,'left',10),
		(projectLabel,'left',10),
		(projectPath,'right',10)
		],
		attachControl=[
		(projectLabel,'top',10,sep_proj),
		(projectPath,'top',6,sep_proj),
		(projectPath,'left',10,projectLabel)
		]
		)

	configForm #finish the form

def LTV_configWindow():

	workspaceName = 'LTV Config'
	if(cmds.workspaceControl(workspaceName, exists=True)):
		cmds.deleteUI(workspaceName)
	cmds.workspaceControl(workspaceName,initialHeight=100,initialWidth=300,uiScript = 'LTV_config_window()')

#LTV_configWindow()
