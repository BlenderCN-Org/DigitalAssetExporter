'''
Created on Sep 25, 2014

@author: haroldserrano
'''
import bpy

class Materials:
    def __init__(self):
        self.diffuse=[]
        self.specular=[]
        self.shininess=0.0
    
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
    def __init__(self):
        self.name=''
        self.hasUV=False
        self.hasMaterials=False
        self.coordinates=Coordinates()
        self.materials=Materials()
        self.texture=Textures()
        self.localSpace=[]
        self.absoluteSpace=[]    

    def unloadModelData(self):
        
        self.unloadCoordinates()
        self.unloadMaterials()
        self.unloadTexture()
        self.unloadLocalSpace()
    
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
        
    def unloadMaterials(self):
        
        if(self.hasMaterials):
            print("<diffuse_color>",end="")
            for d in self.materials.diffuse:
                print("%f %f %f 1.0" %tuple(d),end="")  
            print("</diffuse_color>")    
                
            print("<specular_color>",end="")
            for s in self.materials.specular:
                print("%f %f %f 1.0"%tuple(s),end="")
            print("</specular_color>")    
            
            print("<ambient_color>",end="")    
            print("0.0 0.0 0.0 1.0",end="")
            print("</ambient_color>") 
            
            print("<emission_color>",end="")
            print("0.0 0.0 0.0 1.0",end="")
            print("</emission_color>") 
            
            print("<shininess>",end="")
            print("%f"%self.materials.shininess,end="")
            print("</shininess>")
            print()
            
    def unloadTexture(self):
        
        if(self.hasUV):
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
    
    
class Lights:
    pass

class Camera:
    pass
  
class Loader:
    def __init__(self):
        self.modelList=[]
        
    def r3d(self,v):
        return round(v[0],6), round(v[1],6), round(v[2],6)


    def r2d(self,v):
        return round(v[0],6), round(v[1],6)
    
    
    def start(self):
        
        self.loadModel()
        self.loadLights()
        self.loadCamera()
        
    def writeToFile(self):
        self.unloadModel()
        self.unloadLights()
        self.unloadCamera()
    
    def loadModel(self):
        
        scene=bpy.context.scene
        
        for models in scene.objects:
            
            if(models.type=="MESH"):
                
                model=Model()
                
                #get name of model
                model.name=models.name
                
                
                for vertices in scene.objects[model.name].data.vertices:
                    
                    #get vertices of model
                    
                    model.coordinates.vertices.append(self.r3d(vertices.co))
                    
                    #get normal of model

                    model.coordinates.normal.append(self.r3d(vertices.normal))
                
                for uvCoordinates in scene.objects[model.name].data.uv_layers.active.data:
                    
                    #get uv coordinates of model                    

                    model.coordinates.uv.append(self.r2d(uvCoordinates.uv))
                    model.hasUV=True
                    
                #get index of model
                for indices in scene.objects[model.name].data.loops:
                    
                    model.coordinates.index.append(indices.vertex_index)
                
                #check if model has materials
                
                if(scene.objects[model.name].active_material):
                
                    model.hasMaterials=True
                    
                    materials=scene.objects[model.name].active_material
                        
                    #get diffuse color
                    diffuse_color=materials.diffuse_color
                    
                    model.materials.diffuse.append(diffuse_color)
                    
                    #get specular color
                    specular_color=materials.specular_color
    
                    model.materials.specular.append(specular_color)
    
                    #get shininess of material
                    shininess=materials.specular_hardness
                    
                    model.materials.shininess=shininess
                
                
                #get texture name
                if(model.hasUV):
                    
                    texture=scene.objects[model.name].data.uv_textures.active.data[0].image.name
                    
                    model.texture=texture
                
                #get local matrix
                matrix_local=scene.objects[model.name].matrix_local

                model.localSpace.append(matrix_local)
                
                self.modelList.append(model)
                
                
    def loadLights(self):
        pass
    
    def loadCamera(self):
        pass

    def unloadData(self):
        
        print("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
        print("<ROLDIE xmlns=\"\" version=\"0.0.1\">")
        
        print("<asset>")
        
        self.unloadModel()
        
        
        print("</asset>")
        
        print("</ROLDIE>")
        
        
    def unloadModel(self):
        
        print("<meshes>")
        
        for model in self.modelList:
            
            print("<mesh name=\"%s\">"%model.name)
            
            model.unloadModelData()
            
            print("</mesh>")                                 
            
            print()
        
        print("</meshes>")
    
    def unloadLights(self):
        pass
    
    def unloadCamera(self):
        pass
    
def main():

#bpy.context.scene.objects['Cube'].data.uv_layers.active.data[0].uv

    loader=Loader()
    loader.loadModel()
    loader.unloadData()

if __name__ == '__main__':
    main()