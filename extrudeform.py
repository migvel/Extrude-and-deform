import bpy
from io_curve_svg import import_svg
import re
import cmath
import math
import sys

# functions
def find_object(targetname):
    """ Return index of objects that contains targename in name """
    foundobject=[]
    for index,object in enumerate(bpy.data.objects):
        if(object.name.find(targetname)!=-1):
            foundobject.append(index)        
    return(foundobject)

def log_vertices(filename,mesh):
    """ Logs in a file the  object vertices information """
    FILE = open(filename,"w+")
    for index,vertex in enumerate(mesh.vertices):
        strline = "Vertice: "+str(index)+"; X "+str(vertex.co[0]) +" Y: "+str(vertex.co[1])+" Z: "+str(vertex.co[2])+"\n"
        FILE.write(strline)
    FILE.close()

def deselect_all_objects():
    """ Deselects all objects """
    for object in bpy.data.objects:
        object.select = False


#main class
class ExtrudeForm:
    #class for extruding and object and deform in the xy.
    Name = "ExtrudeForm"

    def __init__(self,curves):
        self.obj = bpy.context.active_object
        bpy.ops.object.convert(target='MESH',keep_original=False)
        self.mesh = 0
        
    def extrude(self,deep,levels):
        """ Extrudes the plane mesh """
        self.mesh  = self.obj.data
        
        #center
        self.get_object_coordinates()        
        self.obj.location = (( -self.xcent , -self.ycent, 0.0))
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

        self.nvertices = len(self.mesh.vertices)
     
        self.create_vertices(deep,levels)
        self.create_faces(levels)
        
        self.create_mesh("newmesh")    
        self.create_object("newobject")

        scene = bpy.context.scene
        scene.objects.link(self.newobject)
        scene.objects.active = self.newobject
        self.newobject.select = True

    def deform(self,method,mathformula1,mathformula2):
        """ deform the object with different formulas """
        if(method == "orthogonal"):
            self.modify_orthogonal_mesh(mathformula1,mathformula2)
        elif(method == "polar"):
            self.modify_polar_mesh(mathformula1,mathformula2)

    def create_vertices(self,deep,levels):
        """ Create vertices of extrusion """
        self.vertices = []
        for zlevel in range(0,deep,int(deep/levels)):
            for idx,vertex in enumerate(self.mesh.vertices):
                self.vertices.append((vertex.co[0],vertex.co[1],zlevel))
    
    def create_faces(self,nlevels):
        """ Create the faces for all the mesh """
        self.faces = []
        for levels in range(nlevels-1):
            for vertex in range(self.nvertices):
                self.create_face(vertex + levels * self.nvertices)
                self.faces.append(self.face)
    
    def create_face(self,vertexindex):
        """ Make an square face starting in index counter clockwise """
        self.find_above_vertex(vertexindex)
        purevertex = self.abovevertex - (int(self.abovevertex / self.nvertices) * self.nvertices)

        if(purevertex == self.nvertices-1):
            aboveleftvertex = ( int(self.abovevertex / self.nvertices) * self.nvertices)
        else:
            aboveleftvertex = self.abovevertex+1

        self.find_bellow_vertex(aboveleftvertex)
        self.face = []

        self.face.append(vertexindex)
        self.face.append(self.abovevertex)
        self.face.append(aboveleftvertex)
        self.face.append(self.bellowleftvertex)

    def create_mesh(self,meshname):
        """ create mesh from vertices and sides """
        self.newmesh = bpy.data.meshes.new(meshname)
        self.newmesh.from_pydata(self.vertices, [], self.faces)
        self.newmesh.update()

    def create_object(self,objectname):
        self.newobject = bpy.data.objects.new(objectname,self.newmesh)
        self.newobject.data = self.newmesh

    def modify_polar_mesh(self,mathstringphi,mathstringr):
        """ Modifies in a polar way a mesh """
        for idx,vertex in enumerate(self.newmesh.vertices):
            r = p  = int(idx / self.nvertices)
            r,phi = cmath.polar(complex(vertex.co[0],vertex.co[1]))

            if(mathstringr != ""):
                self.math_parser(mathstringr)
                modr = eval(self.formula)
                r = r + modr

            if(mathstringphi != ""):
                self.math_parser(mathstringphi)
                modphi = eval(self.formula)
                phi = phi + modphi
        
            n = cmath.rect(r,phi)
            vertex.co[0]= n.real
            vertex.co[1] = n.imag       

    def modify_orthogonal_mesh(self,mathstringx,mathstringy):
        """ Modifies in a orthogonal way a mesh """ 
        for idx,vertex in enumerate(self.newmesh.vertices):
            
            x = y = int(idx / self.nvertices)
            if(mathstringx != ""):
                self.math_parser(mathstringx)
                modx = eval(self.formula)
                vertex.co[0] = vertex.co[0] * modx
        
            if(mathstringy != ""):
                self.math_parser(mathstringy)
                mody = eval(self.formula)
                vertex.co[1] = vertex.co[1] * mody

            
    def get_object_coordinates(self):
        """ Returns the object distance to center """
        xmax = xmin = self.mesh.vertices[0].co[0]
        ymax = ymin = self.mesh.vertices[0].co[1]

        for index,vertex in enumerate(self.mesh.vertices):
            if(vertex.co[0]>xmax):
                xmax = vertex.co[0]
            elif(vertex.co[0]<xmin):
                xmin = vertex.co[0]
            if(vertex.co[1]>ymax):
                ymax = vertex.co[1]
            elif(vertex.co[1]<ymin):
                ymin = vertex.co[1]
            
        self.xcent = xmax - (xmax - xmin ) / 2
        self.ycent = ymax - (ymax - ymin ) / 2

    def find_above_vertex(self,vertexindex):
        """ finds vertex above from a given one """
        self.abovevertex = vertexindex+self.nvertices

    def find_bellow_vertex(self,vertexindex):
        """ finds vertex bellow from given one """
        self.bellowleftvertex =  vertexindex-self.nvertices

    def math_parser(self,string):
        """ pases a math formula into math module sintax """
        symbols=['sin','cos','exp','pi','log','sqrt']
        self.formula=string
        for isymbol in symbols:
            p = re.compile(isymbol)
            for i in p.finditer(self.formula):
               self.formula = self.formula[:i.start()]+'math.'+self.formula[i.start():]
               

                                        
                
a = ExtrudeForm("hola")
a.extrude(10,10)
#a.deform("polar","p*0.1","r*0.4")
a.deform("orthogonal","sqrt(0.1*x)+1","sqrt(0.1*y)+1")

# ("p*0.1","")
# ("0.3*exp(x)+5","0.3*exp(y)+5")
# ("sqrt(x)+1","")
# ("sqrt(x)+1","sqrt(y)+1")
# ("abs(sin(x))+3","abs(sin(y))+3")
