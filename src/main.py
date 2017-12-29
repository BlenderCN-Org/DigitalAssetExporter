'''
Created on Sep 25, 2014

Digital Asset Loader script for the Untold Engine

@author: Harold Serrano
'''
import bpy
import mathutils
import operator
import copy
from math import radians
from math import degrees

#class to write to a file

class ExportFile:
    def __init__(self, filePath):
        self.filePath=filePath
        self.fileToWrite=None
        
    def openFile(self):
        self.fileToWrite=open(self.filePath, 'w', encoding='utf-8')
        
    
    def writeData(self, dataToWrite):
        
        self.fileToWrite.write(dataToWrite)

    def writeData(self, dataToWrite, space=None):
        
        self.fileToWrite.write(dataToWrite+' ')
        
    
    def closeFile(self):
        self.fileToWrite.close()
        
        
        return {'FINISHED'}


class PointLights:
    def __init__(self):
        self.name=None
        self.energy=None
        self.localSpace=[]
        self.color=[]
        
    def unloadPointLightData(self):
        
        print("<energy>%f</energy>"%self.energy)
        
        print("<light_color>",end="")
        for s in self.color:
            print("%f %f %f 1.0"%tuple(s),end="")
        print("</light_color>") 
        
        print("<local_matrix>",end="")
        for m in self.localSpace:
            print("%f %f %f %f "%tuple(m.row[0]),end="")
            print("%f %f %f %f "%tuple(m.row[1]),end="")
            print("%f %f %f %f "%tuple(m.row[2]),end="")
            print("%f %f %f %f"%tuple(m.row[3]),end="")
        print("</local_matrix>")
        
        
    
class Animation:
    def __init__(self):
        self.name=None
        self.keyframes=[]
        self.fps=None
    
class Keyframe:
    def __init__(self):
        self.time=None
        self.animationBonePoses=[]

class AnimationBonePoses:
    def __init__(self):
        self.name=None
        self.pose=[]    
    
class Bone:
    def __init__(self):
        self.name=None
        self.parent=None
        self.boneObject=None
        self.vertexGroupIndex=None
        self.localMatrix=None
        self.absoluteMatrix=None
        self.inverseBindPoseMatrix=None
        self.bindPoseMatrix=None
        self.restPoseMatrix=None
        self.vertexWeights=[]
        self.localMatrixList=[]
        self.inverseBindPoseMatrixList=[]
        self.bindPoseMatrixList=[]
        self.restPoseMatrixList=[]
        self.index=None
        
    
class Armature:
    def __init__(self,world):
        self.name=None
        self.armatureObject=None
        self.absoluteMatrix=None
        self.localMatrix=None
        self.rootBone=None
        self.childrenBones=[]
        self.vertexGroupWeight=[]
        self.vertexGroupDict={}
        self.numberOfBones=None
        self.bones=[]
        self.animations=[]
        self.hasAnimation=False
        self.world=world
        self.bindShapeMatrix=[]
        self.accumulatedParentMatrix=[]
        self.listOfParents=[]
        self.modelerAnimationSpaceTransform=[]
        
    def getListOfParents(self,bone):
        
        if(bone.parent==None):
            #self.listOfParents.append(bone.name)
            return 1
        else:
            self.listOfParents.append(bone.parent)
            self.getListOfParents(bone.parent)
        
    def setAllBones(self):
        
        rootBone=self.armatureObject.data.bones[0]
        
        self.childrenBones.append(rootBone)
        
        self.loadChildrenBones(rootBone)

        
    def loadChildrenBones(self,bone):
        
        for children in bone.children:    
            
            self.childrenBones.append(children)
            
            self.loadChildrenBones(children)
            
    def loadBonesInfo(self):
        
        #get total count of bones
        self.numberOfBones=len(self.childrenBones)
        
        #get the armature absolute matrix
        self.absoluteMatrix=self.armatureObject.matrix_world
        
        
        for bones in self.childrenBones:
            
            bone=Bone()
            
            #get bone name
            bone.name=bones.name
            
            #get bone local matrix
            
            if(bones.parent==None):
                #set bone parent
                bone.parent='root'
                #set local matrix
                bone.localMatrix=bones.matrix_local
                #set absolute matrix
                bone.absoluteMatrix=bone.localMatrix
                #set bind pose
                bone.bindPoseMatrix=bone.absoluteMatrix
                #set inverse bind pose
                bone.inverseBindPoseMatrix=bones.matrix_local.inverted()
                
                
            else:
                
                #clear the list
                self.listOfParents.clear()
                self.accumulatedParentMatrix=mathutils.Matrix.Identity(4)
                #set bone parent
                bone.parent=bones.parent.name
                #set local matrix
                bone.localMatrix=bones.matrix_local
                #set absolute matrix
                
                self.getListOfParents(bones)
                self.listOfParents.reverse()
                
                #the following for loops gets the right pose matrix for each parent of the current bone.
                #here is a pseudo example of what is happening
                #if(k==1): //bone 1..not root bone
                  #  bone.absoluteMatrix=bones.parent.matrix_local.inverted()*bones.matrix_local
                    
                    
                 #   grandPapMatrix=bones.parent.matrix_local.inverted()*bones.matrix_local
                    
                #if(k==2): //bone 2
                #    bone.absoluteMatrix=grandPapMatrix.inverted()*bones.matrix_local
                
                for parentBones in self.listOfParents:
                    
                    self.accumulatedParentMatrix=self.accumulatedParentMatrix*parentBones.matrix_local
                    
                    self.accumulatedParentMatrix=self.accumulatedParentMatrix.inverted()
                    
                
                bone.absoluteMatrix=self.accumulatedParentMatrix*bones.matrix_local
                
                #set bind pose
                bone.bindPoseMatrix=bone.absoluteMatrix
                #set bind pose inverse
                bone.inverseBindPoseMatrix=bones.matrix_local.inverted()
                
            #look for the vertex group
            bone.index=self.vertexGroupDict[bone.name]

            #get vertex weights for bone            
            for i in range(0,len(self.vertexGroupWeight),self.numberOfBones):
                
                bone.vertexWeights.append(self.vertexGroupWeight[bone.index+i])
                
            #append matrix data to list
            bone.localMatrixList.append(copy.copy(bone.localMatrix))
            bone.bindPoseMatrixList.append(copy.copy(bone.bindPoseMatrix))
            bone.inverseBindPoseMatrixList.append(copy.copy(bone.inverseBindPoseMatrix))
            
            #attach bone to armature class
            
            self.bones.append(bone)

    def unloadBones(self):
        
        print("<armature>",end="")
        
        print()
        print("<bind_shape_matrix>",end="")
        for m in self.bindShapeMatrix:
            print("%f %f %f %f "%tuple(m.row[0]),end="")
            print("%f %f %f %f "%tuple(m.row[1]),end="")
            print("%f %f %f %f "%tuple(m.row[2]),end="")
            print("%f %f %f %f"%tuple(m.row[3]),end="")
        print("</bind_shape_matrix>")
        
        for bone in self.bones:
            print()
            print("<bone name=\"%s\" parent=\"%s\">"%(bone.name,bone.parent))
            print("<local_matrix>",end="")
            for m in bone.localMatrixList:
                print("%f %f %f %f "%tuple(m.row[0]),end="")
                print("%f %f %f %f "%tuple(m.row[1]),end="")
                print("%f %f %f %f "%tuple(m.row[2]),end="")
                print("%f %f %f %f"%tuple(m.row[3]),end="")
            print("</local_matrix>")
            
            print("<bind_pose_matrix>",end="")
            for m in bone.bindPoseMatrixList:
                print("%f %f %f %f "%tuple(m.row[0]),end="")
                print("%f %f %f %f "%tuple(m.row[1]),end="")
                print("%f %f %f %f "%tuple(m.row[2]),end="")
                print("%f %f %f %f"%tuple(m.row[3]),end="")
            
            print("</bind_pose_matrix>")
            
            print("<inverse_bind_pose_matrix>",end="")
            for m in bone.inverseBindPoseMatrixList:
                print("%f %f %f %f "%tuple(m.row[0]),end="")
                print("%f %f %f %f "%tuple(m.row[1]),end="")
                print("%f %f %f %f "%tuple(m.row[2]),end="")
                print("%f %f %f %f"%tuple(m.row[3]),end="")
                
            print("</inverse_bind_pose_matrix>")
            
            print("<rest_pose_matrix>",end="")
            for m in bone.restPoseMatrixList:
                print("%f %f %f %f "%tuple(m.row[0]),end="")
                print("%f %f %f %f "%tuple(m.row[1]),end="")
                print("%f %f %f %f "%tuple(m.row[2]),end="")
                print("%f %f %f %f"%tuple(m.row[3]),end="")
                
            print("</rest_pose_matrix>")
            
            print("<vertex_weights weight_count=\"%d\">"%(len(bone.vertexWeights)),end="")
            for vw in bone.vertexWeights:
                print("%f "%vw,end="")
            print("</vertex_weights>")
            
            print("</bone>")
        
        
        print("</armature>")
        
        print()
    
    def frameToTime(self,frame):
        fps=bpy.context.scene.render.fps
        rawTime=frame/fps
        return round(rawTime,3)
        
        
    def setAnimations(self):
        
        actions=bpy.data.actions
        
        scene=bpy.context.scene
        
        if(len(actions)>0):
            
            self.hasAnimation=True
            
            for action in actions:
                #create an animation object
                
                animation=Animation()
                animation.name=action.name
                animation.fps=bpy.context.scene.render.fps
                
                #create a keyframe dictionary needed to store and then sort the keyframes
                keyframeDict={}
                
                
                for fcurves in action.fcurves:
                    for keyframe in fcurves.keyframe_points:
                        
                        #check if the keyframe exist
                        if(keyframeDict.get(keyframe.co[0]) is None):
                        
                            keyframeDict[keyframe.co[0]]=keyframe.co[0]
                
                #sort the dictionary
                sortedKeyframes=sorted(keyframeDict.items(),key=operator.itemgetter(0))
                
                #get keyframes in sorted ascending order
                for keyframes in sortedKeyframes:
                    
                    #for each keyframe, create an object
                    keyframe=Keyframe()
                    #set the keyframe time
                    keyframe.time=self.frameToTime(keyframes[1])
                    
                    #set the scene to the keyframe
                    scene.frame_set(keyframes[1])
                    #update the scene
                    
                    #get the pose for each bone at that timeline
                    for bones in self.childrenBones:
                        
                        animationBonePose=AnimationBonePoses()
                        animationBonePose.name=bones.name
                        
                        parentBoneSpace=mathutils.Matrix.Identity(4)
                        childBoneSpace=mathutils.Matrix.Identity(4)
                        finalBoneSpace=mathutils.Matrix.Identity(4)
                         
                        if(bones.parent==None):
                            
                            parentBoneSpace=self.armatureObject.pose.bones[bones.name].matrix*parentBoneSpace
                    
                            finalBoneSpace=parentBoneSpace
                            
                        else:
                               
                            parentBoneSpace=self.armatureObject.pose.bones[bones.name].parent.matrix.inverted()*parentBoneSpace
                            
                            childBoneSpace=self.armatureObject.pose.bones[bones.name].matrix*childBoneSpace
                            
                            childBoneSpace=parentBoneSpace*childBoneSpace
                            
                            finalBoneSpace=childBoneSpace
                            
                        
                        animationBonePose.pose.append(copy.copy(finalBoneSpace))
                            
                        keyframe.animationBonePoses.append(animationBonePose)
                        
                    
                    #append the keyframes to the animation
                    animation.keyframes.append(keyframe)
                
                #append the animation to the armature
                self.animations.append(animation)    
                    
    
    def unloadAnimations(self):
        
        if(self.hasAnimation is True):
            
            print("<animations>")
            
            print("<modeler_animation_transform>",end="")
            for m in self.modelerAnimationSpaceTransform:
                print("%f %f %f %f "%tuple(m.row[0]),end="")
                print("%f %f %f %f "%tuple(m.row[1]),end="")
                print("%f %f %f %f "%tuple(m.row[2]),end="")
                print("%f %f %f %f"%tuple(m.row[3]),end="")
            print("</modeler_animation_transform>")
            
            print()
            for animation in self.animations:
                #print animations
                print("<animation name=\"%s\" fps=\"%f\">"%(animation.name,animation.fps))
                
                for keyframe in animation.keyframes:
                    
                    #print keyframe time
                    print("<keyframe time=\"%f\">"%keyframe.time)
                    
                    for bonePoses in keyframe.animationBonePoses:
                        
                        #print bone poses
                        print("<pose_matrix name=\"%s\">"%bonePoses.name,end="")
                        
                        for m in bonePoses.pose:
                            print("%f %f %f %f "%tuple(m.row[0]),end="")
                            print("%f %f %f %f "%tuple(m.row[1]),end="")
                            print("%f %f %f %f "%tuple(m.row[2]),end="")
                            print("%f %f %f %f"%tuple(m.row[3]),end="")
                        
                        print("</pose_matrix>")
                        
                    print("</keyframe>")
                
                print("</animation>")
            print("</animations>")             
            

class Materials:
    def __init__(self):
        self.name=''
        self.diffuse=[]
        self.specular=[]
        self.diffuse_intensity=[]
        self.specular_intensity=[] 
        self.specular_hardness=[]  
    
class Coordinates:
    def __init__(self):
        self.vertices=[]
        self.normal=[]
        self.uv=[]
        self.index=[]


class Textures:
    def __init__(self):
        self.texture=''

class Model:
    def __init__(self,world):
        self.name=''
        self.vertexCount=''
        self.indexCount=''
        self.dimension=[]
        self.hasUV=False
        self.hasTexture=False
        self.hasMaterials=False
        self.hasArmature=False
        self.hasAnimation=False
        self.coordinates=Coordinates()
        self.materials=Materials()
        self.materialIndex=[]
        self.texture=Textures()
        self.localSpace=[]
        self.absoluteSpace=[]
        self.armature=None
        self.vertexGroupWeight=[] 
        self.vertexGroupDict={}   
        self.worldMatrix=world
        self.prehullvertices=[]
        
    def unloadModelData(self):
        
        self.unloadCoordinates()
        self.unloadHull()
        self.unloadMaterialIndex()
        self.unloadMaterials()
        self.unloadTexture()
        self.unloadLocalSpace()
        self.unloadArmature()
        self.unloadAnimations()
        self.unloadDimension()
    
    def unloadCoordinates(self):
                
        print("<vertices>",end="")
            
        for i in range(0,len(self.coordinates.vertices)):
            
            print("%f %f %f "%tuple(self.coordinates.vertices[i]),end="")   
                
        print("</vertices>")
        
        print()
        
        print("<normal>",end="")
        
        for i in range(0,len(self.coordinates.normal)):
            
            print("%f %f %f "%tuple(self.coordinates.normal[i]),end="")
                     
        print("</normal>")
        
        print()
            
        if(self.hasUV):
            
            print("<uv>",end="")
        
            for i in range(0,len(self.coordinates.uv)):
                
                print("%f %f "%tuple(self.coordinates.uv[i]),end="")
                   
            print("</uv>")
            
            print() 
    
        print("<index>",end="")
        
        for i in self.coordinates.index:
            print("%d "%i,end="")
        
        print("</index>")
        
        print()
        
    def unloadHull(self):
        
        print("<prehullvertices>",end="")
            
        for i in range(0,len(self.prehullvertices)):
            
            print("%f %f %f "%tuple(self.prehullvertices[i]),end="")   
                
        print("</prehullvertices>")
        
        print()
            
    def unloadMaterials(self):
        
        if(self.hasMaterials):
            print("<diffuse_color>",end="")
            for d in self.materials.diffuse:
                print("%f %f %f 1.0 " %tuple(d),end="")  
            print("</diffuse_color>")    
                
            print("<specular_color>",end="")
            for s in self.materials.specular:
                print("%f %f %f 1.0 "%tuple(s),end="")
            print("</specular_color>")    
            
            print("<diffuse_intensity>",end="")
            for di in self.materials.diffuse_intensity:
                print("%f " %di,end="")
            print("</diffuse_intensity>")       
            
            print("<specular_intensity>",end="")
            for si in self.materials.specular_intensity:
                print("%f " %si,end="")
            print("</specular_intensity>") 
            
            print("<specular_hardness>",end="")
            for sh in self.materials.specular_hardness:
                print("%f " %sh,end="")
            print("</specular_hardness>") 
    
            print()
    
    def unloadMaterialIndex(self):
        if(self.hasMaterials):
            print("<material_index>",end="")
            for i in self.materialIndex:
                print("%d " %i,end="")  
            print("</material_index>")  
            print()
                
    def unloadTexture(self):
        
        if(self.hasTexture):
            print("<texture_image>%s</texture_image>"%self.texture)
            
            print()
    
    def unloadLocalSpace(self):
        
        print("<local_matrix>",end="")
        for m in self.localSpace:
            print("%f %f %f %f "%tuple(m.row[0]),end="")
            print("%f %f %f %f "%tuple(m.row[1]),end="")
            print("%f %f %f %f "%tuple(m.row[2]),end="")
            print("%f %f %f %f"%tuple(m.row[3]),end="")
        print("</local_matrix>")
        
        print()
        
    def unloadArmature(self):
        
        if(self.hasArmature):
            self.armature.unloadBones()
    
    def setArmature(self):
        self.armature.setRootBone()
        
    def unloadAnimations(self):
        
        if(self.hasArmature):
            if(self.armature.hasAnimation):
                self.armature.unloadAnimations()   
        
    def unloadDimension(self):
        
        print("<dimension>",end="")
            
        for dimension in self.dimension:
            print("%f %f %f"%tuple(dimension),end="")  
                
        print("</dimension>")
        
        print()
        
class Lights:
    pass

class Camera:
    pass

class World:
    def __init__(self):
        self.metalSpaceTransform=[]
        self.metalLocalSpaceTransform=[]
        self.metalAnimationSpaceTransform=[]
        self.metalArmatureSpaceTransform=[]
        self.metalParentAnimationSpaceTransform=[]
  
class Loader:
    def __init__(self):
        self.modelList=[]
        self.pointLightsList=[]
        self.cameraList=[]
        self.world=None
        
    def r3d(self,v):
        return round(v[0],6), round(v[1],6), round(v[2],6)


    def r2d(self,v):
        return round(v[0],6), round(v[1],6)
    
    
    def start(self):
        
        self.loadModel()
        self.loadPointLights()
        self.loadCamera()
        
    def writeToFile(self):
        self.unloadModel()
        self.unloadPointLights()
        self.unloadCamera()
    
    def loadModel(self):
        
        scene=bpy.context.scene
        
        #get world matrix
        world=World()
        #convert world to metal coords
        world.metalSpaceTransform=mathutils.Matrix.Identity(4)
        world.metalSpaceTransform*=mathutils.Matrix.Scale(-1, 4, (0,0,1))
        world.metalSpaceTransform*=mathutils.Matrix.Rotation(radians(90), 4, "X")
        world.metalSpaceTransform*=mathutils.Matrix.Scale(-1, 4, (0,0,1))

        #metal transformation
        world.metalSpaceTransform *= mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
        world.metalSpaceTransform *= mathutils.Matrix.Rotation(radians(180), 4, "Z")


        world.metalLocalSpaceTransform=mathutils.Matrix.Identity(4)
        world.metalLocalSpaceTransform*=mathutils.Matrix.Rotation(radians(90),4,"X")
        world.metalLocalSpaceTransform*=mathutils.Matrix.Scale(-1,4,(0,0,1))


        world.metalArmatureSpaceTransform=mathutils.Matrix.Identity(4)
        world.metalArmatureSpaceTransform*=mathutils.Matrix.Rotation(radians(90),4,"X")
        world.metalArmatureSpaceTransform*=mathutils.Matrix.Scale(-1,4,(0,0,1))

        # metal transformation
        world.metalArmatureSpaceTransform *= mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
        world.metalArmatureSpaceTransform *= mathutils.Matrix.Rotation(radians(180), 4, "Z")
        
        world.metalModelerAnimationSpaceTransform=mathutils.Matrix.Identity(4)
        world.metalModelerAnimationSpaceTransform*=mathutils.Matrix.Scale(-1, 4, (0,0,1))
        world.metalModelerAnimationSpaceTransform*=mathutils.Matrix.Rotation(radians(90), 4, "X")
        world.metalModelerAnimationSpaceTransform*=mathutils.Matrix.Scale(-1, 4, (0,0,1))

        # metal transformation
        world.metalModelerAnimationSpaceTransform *= mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
        world.metalModelerAnimationSpaceTransform *= mathutils.Matrix.Rotation(radians(180), 4, "Z")

        world.metalModelerAnimationSpaceTransform=world.metalModelerAnimationSpaceTransform.inverted()
        
        
        self.world=world
        
        #get all models in the scene
        for models in scene.objects:
            
            if(models.type=="MESH"):


                #triangularized the models

                # set the model as active
                scene.objects.active = models

                # put the model in edit mode
                bpy.ops.object.mode_set(mode='EDIT')

                # select all parts of the model
                bpy.ops.mesh.select_all(action='SELECT')

                # triangulize the model
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

                # put the model back in normal mode
                bpy.ops.object.mode_set(mode='OBJECT')

                #end triangularization
                
                model=Model(world)
                
                #get name of model
                model.name=models.name
                
                #get local matrix
                matrix_local=world.metalLocalSpaceTransform*scene.objects[model.name].matrix_local*world.metalLocalSpaceTransform
                
                #negate the z-axis
                #matrix_local[2][3]=-matrix_local[2][3]
                
                model.localSpace.append(matrix_local)
                
                #get absolute matrix
                model.absoluteSpace.append(scene.objects[model.name].matrix_world)
                
                 #get index of model
                for i,indices in enumerate(scene.objects[model.name].data.loops):
                    
                    #get vertices of model
                    
                    vertex=scene.objects[model.name].data.vertices[indices.vertex_index].co
                    
                    #convert vertex to metal coordinate
                    vertex=world.metalSpaceTransform*vertex                
                    
                    vertex=self.r3d(vertex)
                    
                    model.coordinates.vertices.append(vertex)
                    
                    #get normal of model
                    
                    normal=scene.objects[model.name].data.vertices[indices.vertex_index].normal
                    
                    #convert normal to metal coordinate
                    normal=world.metalSpaceTransform*normal
                    
                    normal=self.r3d(normal)
                    
                    model.coordinates.normal.append(normal)
                    
                    #get vertex weight
                    
                    vertexGroupWeightDict={}  #create a dictionary for the weights
                    
                    for vertexGroup in scene.objects[model.name].data.vertices[indices.vertex_index].groups:
                        
                        vertexGroupWeightDict[vertexGroup.group]=vertexGroup.weight
                        
                    model.vertexGroupWeight.append(vertexGroupWeightDict)
                        
                    #get the index
                    model.coordinates.index.append(i)
                    
                    #get material index
                    #material_index=scene.objects[model.name].data.polygons[indices.vertex_index].material_index
                    #model.materialIndex.append(material_index)
                
                if(scene.objects[model.name].data.uv_layers):
                    for uvCoordinates in scene.objects[model.name].data.uv_layers.active.data:
                        
                        #get uv coordinates of model                    
    
                        model.coordinates.uv.append(self.r2d(uvCoordinates.uv))
                        model.hasUV=True
                    
                #check if model has materials
                
                if(len(scene.objects[model.name].material_slots)<1):

                    meshMaterial=bpy.data.materials.new(name="NewMaterial")
                    scene.objects[model.name].data.materials.append(meshMaterial)

                
                #get material index
                for materialIndex in scene.objects[model.name].data.polygons:
                    #need to append it three for each triangle vertex
                    model.materialIndex.append(materialIndex.material_index)
                    model.materialIndex.append(materialIndex.material_index)
                    model.materialIndex.append(materialIndex.material_index)
                    
                    
                #get model material slots
                for materialSlot in scene.objects[model.name].material_slots:
                    
                    model.materials.diffuse.append(bpy.data.materials[materialSlot.name].diffuse_color)
                    model.materials.specular.append(bpy.data.materials[materialSlot.name].specular_color)
                    model.materials.diffuse_intensity.append(bpy.data.materials[materialSlot.name].diffuse_intensity)
                    model.materials.specular_intensity.append(bpy.data.materials[materialSlot.name].specular_intensity)
                    model.materials.specular_hardness.append(bpy.data.materials[materialSlot.name].specular_hardness)
                    
                model.hasMaterials=True
                
                
                #get texture name
                if(model.hasUV==True):
                    if(scene.objects[model.name].data.uv_textures.active.data[0].image!=None):
                        
                        model.hasTexture=True;
                        
                        texture=scene.objects[model.name].data.uv_textures.active.data[0].image.name
                        
                        model.texture=texture
                
                #get all the vertex groups affecting the object
                for vertexGroups in scene.objects[model.name].vertex_groups:
                    model.vertexGroupDict[vertexGroups.name]=vertexGroups.index
                    
                
                #check if model has armature
                armature=models.find_armature()
            
                if(armature!=None):
                
                    model.hasArmature=True
                    
                    modelArmature=Armature(world)
    
                    modelArmature.armatureObject=armature
                    
                    model.armature=modelArmature
                    
                    #update the metal space of the armature
                    modelArmature.localMatrix=world.metalArmatureSpaceTransform.inverted()*armature.matrix_local*world.metalArmatureSpaceTransform
                    
                    #set name
                    model.armature.name=armature.name
                    
                    #set Bind Shape Matrix
                    model.armature.bindShapeMatrix.append(modelArmature.localMatrix)
                    
                    #set the modeler animation transformation space
                    model.armature.modelerAnimationSpaceTransform.append(world.metalModelerAnimationSpaceTransform)
                    
                    #copy the vertex group from the model to the armature
                    
                    #go throught the vertexGroupWeight, get the dictionary
                    # and fill in with zero any vertex group that does not exist
                    # then append the data to model.armature.vertexGroupWeight
                    
                    for n in model.vertexGroupWeight:
                        for j in range(0,len(model.vertexGroupDict)):
                            if(n.get(j) is None):
                                model.armature.vertexGroupWeight.append(0.0)
                            else:
                                model.armature.vertexGroupWeight.append(n.get(j))
                                
                    
                    #copy vertex group dictionary
                    model.armature.vertexGroupDict=model.vertexGroupDict
                    
                    model.armature.setAllBones()
                    
                    model.armature.loadBonesInfo()
                    
                    model.armature.setAnimations()
                
                #get dimension of object
                model.dimension.append(scene.objects[model.name].dimensions)   
                
                #get the individual vertices to compute convex hull
                for prehullvertices in scene.objects[model.name].data.vertices:
                
                    #get the coordinate
                    prehullvertex=prehullvertices.co
                    
                    #convert vertex to metal coordinate
                    prehullvertex=world.metalSpaceTransform*prehullvertex                
                    
                    prehullvertex=self.r3d(prehullvertex)
                    
                    model.prehullvertices.append(prehullvertex) 
                    
                self.modelList.append(model)
                
    
    def loadPointLights(self):
        
        scene=bpy.context.scene
        
         #get all lights in the scene
        for lights in scene.objects:
            
            if(lights.type=="LAMP"):
                
                if(bpy.data.lamps[lights.name].type=="SUN"):

                    light=PointLights()
                    
                    light.name=lights.name
                    
                    #light color
                    light.color.append(scene.objects[light.name].data.color)
                    
                    #Light energy
                    light.energy=scene.objects[light.name].data.energy
                    
                    #light local space
                    light.localSpace.append(self.world.metalLocalSpaceTransform*scene.objects[light.name].matrix_local*self.world.metalLocalSpaceTransform)
                    
                    #append the lights to the list
                    self.pointLightsList.append(light)
    
    def loadCamera(self):
        pass

    def unloadData(self):
        
        print("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
        print("<UntoldEngine xmlns=\"\" version=\"0.0.1\">")
        
        print("<asset>")
        
        self.unloadModel()
        self.unloadPointLights()
        
        print("</asset>")
        
        print("</UntoldEngine>")
        
        
    def unloadModel(self):
        
        print("<meshes>")
        
        for model in self.modelList:
            
            print("<mesh name=\"%s\" vertex_count=\"%d\" index_count=\"%d\">"%(model.name,len(model.coordinates.vertices),len(model.coordinates.index)))
            
            model.unloadModelData()
            
            print("</mesh>")                                 
            
            print()
        
        print("</meshes>")
        print()
        
    def unloadPointLights(self):
        
        print("<point_lights>")
        for lights in self.pointLightsList:
            print()
            print("<point_light name=\"%s\">"%lights.name)
            
            lights.unloadPointLightData()
            
            print("</point_light>")
            print()
        print("</point_lights>")
        
        print()
    def unloadCamera(self):
        pass
    
def main():

#bpy.context.scene.objects['Cube'].data.uv_layers.active.data[0].uv
    #set scene to frame zero
    scene=bpy.context.scene
    scene.frame_set(0)
    
    #open the file to write
    exportFile=ExportFile("/Users/haroldserrano/Downloads/scripttext.txt")
    exportFile.openFile()

    loader=Loader()
    loader.loadModel()
    loader.loadPointLights()
    
    loader.unloadData()

    #close the file
    exportFile.closeFile()
    

if __name__ == '__main__':
    main()