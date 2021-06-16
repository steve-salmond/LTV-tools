import maya.cmds as cmds

#list cameras
def listAllCameras():
	cameraTransforms = []
	listAllCameras = cmds.listCameras(p=True)
	#remove 'persp' camera
	if 'persp' in listAllCameras: listAllCameras.remove('persp')
	for c in listAllCameras:
		if cmds.objectType(c) == "camera":
			cp = cmds.listRelatives(c,p=True)[0]
			cameraTransforms.append(cp)
		else:
			cameraTransforms.append(c)
	return cameraTransforms

def parentNewCamera(oldCamera):
	#find cameraShape
	camShape = cmds.listRelatives(oldCamera,type='camera')
	oldCamera = [oldCamera]
	oldCamera.append(camShape[0])
	#make new camera
	newCamera = cmds.camera(n='EXPORT_CAM');
	#copy transform attributes
	atttributes = ['rotatePivotX','rotatePivotY','rotatePivotZ','scalePivotX','scalePivotY','scalePivotZ']
	for a in atttributes:
		cmds.connectAttr('%s.%s'%(oldCamera[0],a),'%s.%s'%(newCamera[0],a))
	#constrain new camera to old camera
	cmds.parentConstraint(oldCamera[0],newCamera[0])
	#copy camera attributes
	atttributes = ['focalLength']
	for a in atttributes:
		cmds.connectAttr('%s.%s'%(oldCamera[1],a),'%s.%s'%(newCamera[1],a))
	#set extra attributes
	filmFit = cmds.getAttr('%s.filmFit'%oldCamera[1])
	cmds.setAttr('%s.filmFit'%newCamera[1],filmFit)
	cmds.setAttr('%s.nearClipPlane'%newCamera[1],10)
	cmds.setAttr('%s.farClipPlane'%newCamera[1],100000)
	#return new transform and shape as list
	return newCamera