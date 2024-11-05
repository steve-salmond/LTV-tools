import maya.cmds as cmds
import LTV_utilities.unityConfig as unity

### --- UI --- ###

def changeSelection():
	i=cmds.optionMenu('projSelection',q=True,select=True)
	unity.updatePrefs('active',i-1)

def LTV_config_window():
	configForm = cmds.formLayout() #start the form
	#Unity Project location
	#Variables
	unityProjects,activeProject = unity.getUnityProject() #try find existing config, uses path relative to maya project if non found
	#UI
	projectLabel = cmds.text('projectLabel',label='Project paths',w=100,al='left') #project label
	addProjectButton = cmds.button('addProjectButton',l='Add',h=25,w=100,c='unity.browseToProject()')
	removeProjectButton = cmds.button('removeProjectButton',l='Remove',h=25,w=100,c='',en=False)
	projSelection = cmds.optionMenu('projSelection',cc="changeSelection()")
	for project in unityProjects:
		cmds.menuItem( label=project )
	cmds.optionMenu('projSelection',e=True,select=activeProject+1)
	# UI layout
	cmds.formLayout(
		configForm,
		edit=True,
		attachForm=[
		(removeProjectButton,'right',10),
		(projectLabel,'left',10),
		(projSelection,'right',10),
		(projectLabel,'top',10),
		(addProjectButton,'top',6),
		(removeProjectButton,'top',6)
		],
		attachControl=[
		(addProjectButton,'left',10,projectLabel),
		(removeProjectButton,'left',1,addProjectButton),
		(projSelection,'top',6,addProjectButton),
		(projSelection,'left',10,projectLabel)
		],
		attachPosition=[
		(addProjectButton,'right',5,65),
		]
		)

	configForm #finish the form

def LTV_configWindow():

	workspaceName = 'LTV Config'
	if(cmds.workspaceControl(workspaceName, exists=True)):
		cmds.deleteUI(workspaceName)
	cmds.workspaceControl(workspaceName,initialHeight=50,initialWidth=200,uiScript = 'LTV_config_window()')

#LTV_configWindow()
