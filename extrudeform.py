import bpy
from io_curve_svg import import_svg
import re
import cmath
import math

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

def get_object_center(mesh):
    """ Returns the object distance to center """
    xmax = xmin = mesh.vertices[0].co[0]
    ymax = ymin = mesh.vertices[0].co[1]

    for index,vertex in enumerate(mesh.vertices):
        if(vertex.co[0]>xmax):
            xmax = vertex.co[0]
        elif(vertex.co[0]<xmin):
            xmin = vertex.co[0]
        if(vertex.co[1]>ymax):
            ymax = vertex.co[1]
        elif(vertex.co[1]<ymin):
            ymin = vertex.co[1]
            
    return(abs(xmax) - (abs(xmax) - abs(xmin)) / 2 , abs(ymax) - (abs(ymax) - abs(ymin)) / 2)

def create_mesh(meshname,vertices,sides):
    """ create mesh from vertices and sides """
    newmesh = bpy.data.meshes.new(meshname)
    newmesh.from_pydata(vertices, [], sides)
    newmesh.update()
    return(newmesh)
    
def create_object(objectname,mesh):
    newobject = bpy.data.objects.new(objectname,mesh)
    newobject.data = newmesh
    return(newobject)

def create_vertices(deep,levels):
    """ Create vertices of extrusion """
    vertices = []
    for zlevel in range(0,deep,int(deep/levels)):
        print(int(deep/levels))
        for idx,vertex in enumerate(mesh.vertices):
            vertices.append((vertex.co[0],vertex.co[1],zlevel))
    return(vertices)

def deselect_all_objects():
    """ Deselects all objects """
    for object in bpy.data.objects:
        object.select = False

def create_face(vertexindex,nlayervertices):
    """ Make an square face starting in index counter clockwise """
    abovevertex = find_above_vertex(vertexindex,nlayervertices)
    purevertex = abovevertex - (int(abovevertex / nlayervertices) * nlayervertices)

    if(purevertex == nlayervertices-1):
        aboveleftvertex = ( int(abovevertex / nlayervertices) * nlayervertices)
    else:
        aboveleftvertex = abovevertex+1

    bellowleftvertex = find_bellow_vertex(aboveleftvertex,nlayervertices)
    face = []

    face.append(vertexindex)
    face.append(abovevertex)
    face.append(aboveleftvertex)
    face.append(bellowleftvertex)
    return(face)
    

def create_faces(nlayervertices,nlevels):
    """ Create the faces for all the mesh """
    faces = []
    for levels in range(nlevels-1):
        for vertex in range(nlayervertices):
            face = create_face(vertex + levels * nlayervertices,nlayervertices)
            faces.append(face)
    return(faces)

def find_above_vertex(vertexindex,nlayervertices):
    """ finds vertex above from a given one """
    return(vertexindex+nlayervertices)

def find_bellow_vertex(vertexindex,nlayervertices):
    """ finds vertex bellow from given one """
    return(vertexindex-nlayervertices)

def modify_polar_mesh(mathstringphi,mathstringr,mesh,nlayervertices):
    """ Modifies in a polar way a mesh """

    for idx,vertex in enumerate(mesh.vertices):
        r = p  = int(idx / nlayervertices)
        
        r,phi = cmath.polar(complex(vertex.co[0],vertex.co[1]))

        if(mathstringr != ""):
            formular = math_parser(mathstringr)
            modr = eval(formular)
            r = r + modr
        if(mathstringphi != ""):
            formulaphi = math_parser(mathstringphi)
            modphi = eval(formulaphi)
            phi = phi + modphi
        
        n = cmath.rect(r,phi)
        vertex.co[0]= n.real
        vertex.co[1] = n.imag       

    return(mesh)
        
def modify_orthogonal_mesh(mathstringx,mathstringy,mesh,nlayervertices):
    """ Modifies in a orthogonal way a mesh """ 
    for idx,vertex in enumerate(mesh.vertices):

        x = y = int(idx / nlayervertices)
        
        formulax = math_parser(mathstringx)
        formulay = math_parser(mathstringy)
        
        if(mathstringx != ""):
            modx = eval(formulax)
            vertex.co[0] = vertex.co[0] * modx
        
        if(mathstringy != ""):
            mody = eval(formulay)
            vertex.co[1] = vertex.co[1] * mody

    return(mesh)


def math_parser(string):
    """ pases a math formula into math module sintax """
    symbols=['sin','cos','exp','pi','log','sqrt']

    for isymbol in symbols:
        p = re.compile(isymbol)
        for i in p.finditer(string):
            string=string[:i.start()]+'math.'+string[i.start():]
    return(string)


# main
print("Importing svg file")
import_svg.load_svg("path to svg file to import")

idx = find_object("Curve")

object = bpy.data.objects[idx[0]]
object.select=1
bpy.context.scene.objects.active = object
bpy.ops.object.convert(target='MESH',keep_original=False)

mesh = object.data
nvertices = len(mesh.vertices)

log_vertices("/home/sio2/logvertices.log",mesh)

xcent,ycent = get_object_center(mesh)
object.location=(-xcent, ycent, 0)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

vertices = create_vertices(10,10)
faces = create_faces(nvertices,10)

newmesh = create_mesh("newmesh",vertices,faces)    
newobject =  create_object("newobject",newmesh)

scene = bpy.context.scene
scene.objects.link(newobject)
scene.objects.active = newobject
newobject.select = True

deselect_all_objects()
idx = find_object("Curve")
object = bpy.data.objects[idx[0]]
object.select=1
bpy.ops.object.delete()

#newmesh = modify_polar_mesh("p*0.1","r*0.4",newmesh,nvertices)
newmesh = modify_polar_mesh("p*0.1","",newmesh,nvertices)
#newmesh = modify_orthogonal_mesh("0.3*exp(x)+5","0.3*exp(y)+5",newmesh,nvertices)
#newmesh = modify_orthogonal_mesh("sqrt(x)+1","",newmesh,nvertices)
newmesh = modify_orthogonal_mesh("sqrt(x)+1","sqrt(y)+1",newmesh,nvertices)
#newmesh = modify_orthogonal_mesh("abs(sin(x))+3","abs(sin(y))+3",newmesh,nvertices)
