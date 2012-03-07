#!BPY

"""
Name: 'OpenGL (.c)...'
Blender: 232
Group: 'Export'
Tooltip: 'Save to a C source file'
"""

################################################################################
#
#  BLENDER TO OPENGL EXPORTER
#
#  MAINTAINED BY: cosmiczilch@gmail.com
#
#  Notes from raphael:
# 
# * Scaling and deformations:
#   These are not handled in the script, you MUST select all objects
#   of the scene and select
#   Transform -> Clear/Apply -> Apply Size/Rotation  (Ctrl+A)
#   Transform -> Clear/Apply -> Apply Deformation  (Shift+Ctrl+A)
#   before exporting in order to have correct transformations
#   in the exported file.
# 
################################################################################

#==================================================#
# New name based on old with a different extension #
#==================================================#
def newFName(ext):
	return Blender.Get('filename')[: -len(Blender.Get('filename').split('.', -1)[-1]) ] + ext

import Blender
from Blender import Object, NMesh
	
# My Co class
class Co:
	x = 0.0
	y = 0.0
	z = 0.0
	def __init__(self, arg1, arg2, arg3):
		self.x = arg1
		self.y = arg2
		self.z = arg3
		

# My No class
class No:
	x = 0.0
	y = 0.0
	z = 0.0
	def __init__(self, arg1, arg2, arg3):
		self.x = arg1
		self.y = arg2
		self.z = arg3
	
# My Uv class
class Uvco:
	x = 0.0
	y = 0.0
	def __init__(self, arg1, arg2):
		self.x = arg1
		self.y = arg2

# MyVert class
class MyVert:
	co = Co(0.0, 0.0, 0.0)

	index = 0

	no = No(0.0, 0.0, 0.0)
	uvco = Uvco(0.0, 0.0)

	def __init__(self, arg1, arg2, arg3):
		self.co.x = arg1
		self.co.y = arg2
		self.co.z = arg3
# /MyVert class


def save_opengl(filename):
	
	# Open file
	f = open(filename+".c","w")
	header_file = open(filename+".h", "w")
	
	print "File %s created and opened. Now exporting..." % filename
	
	# Write all the preprocessors in the header file required to
	# make it work w/ vbo_Utilities.h :
	header_file.write("#ifndef MODEL_H")
	header_file.write("\n#define MODEL_H")

	header_file.write("\n\n#include <GL/gl.h>")
	header_file.write("\n#include <GL/glu.h>")
	header_file.write("\n\n#include \"vbo_Utilities.h\"")
	header_file.write("\n#include \"cpolymodel.h\"")

	header_file.write("\n\n// The following is the list of objects that will be exported : \n")
	# The actual object names and their estern declarations will be written out in the loop below

	f.write("#include \"%s.h\"\n\n" % filename)

	# Which object to export
	# currently all objects (meshes only - see below)
	objects = [ob for ob in Object.GetSelected() if ob.getType() == 'Mesh']
	
	obj_index = 0
	for obj in objects:
		nmesh = NMesh.GetRawFromObject(obj.name)
	
		header_file.write("\nextern CPolyModel %s;" % (nmesh.name))
		header_file.write("\n\nvoid initialize_all_models ();")
		header_file.write("\nvoid ready_all_models_for_render ();")

		f.write("\n// Object: %s" % (nmesh.name))
		f.write("\nCPolyModel %s;" % (nmesh.name))
		f.write("\n\nvoid make_%s_vbo_arrays () {" % (nmesh.name))

		# Get the list of vertices for the object
		vertices = nmesh.verts[:]
		# Get the list of faces for the object
		faces = nmesh.faces[:]
		# initialize a refCount array for the vertices
		refCount_for_vertices = []
		for idx in range(len(vertices)):
			refCount_for_vertices.append(0)

		# Make one pass through all the faces in the object
		# to identify all the vertices that will have to be split
		# into 2 or more vertices if they have different texture coordinates
		# as part of different faces. Example : vertices along uv-unwrapping_seams. 
		# Naturally, this has to be done only if the mesh uses face-UV textures

		if nmesh.hasFaceUV():
			for face in faces:
				for idx in range(len(face.v)):
					vertex_idx = face.v[idx].index
					if refCount_for_vertices[vertex_idx] == 0:
						refCount_for_vertices[vertex_idx] = 1
						vertices[vertex_idx].uvco.x = face.uv[idx][0]
						vertices[vertex_idx].uvco.y = face.uv[idx][1]
					elif face.uv[idx][0] != vertices[vertex_idx].uvco.x or face.uv[idx][1] != vertices[vertex_idx].uvco.y:
						refCount_for_vertices.append(1)
						# get a new temp vert of type MyVert
						newVert = MyVert(0.0, 0.0, 0.0)

						# Copy over relevant stuff to newVert
						newVert.co = Co(vertices[vertex_idx].co.x, vertices[vertex_idx].co.y, vertices[vertex_idx].co.z)

						newVert.index = vertices[vertex_idx].index

						newVert.no = No(vertices[vertex_idx].no.x, vertices[vertex_idx].no.y, vertices[vertex_idx].no.z)

						# newVert.uvco.x = vertices[vertex_idx].uvco.x
						# newVert.uvco.y = vertices[vertex_idx].uvco.y
						newVert.uvco = Uvco(vertices[vertex_idx].uvco.x, vertices[vertex_idx].uvco.y)

						# Append it to the list
						vertices.append( newVert )

						vertex_idx = len(vertices) - 1		# new vertex_idx, of the newly appended vertex

						# Now set the diverged uvco and index at the newly appended vertex
						vertices[vertex_idx].uvco.x = face.uv[idx][0]
						vertices[vertex_idx].uvco.y = face.uv[idx][1]
						vertices[vertex_idx].index = vertex_idx

						# And, set the face's v to point to this newly appended vertex
						face.v[idx] = vertices[vertex_idx]
					
		numVerts = len(vertices)
		f.write("\n\tint numVertices = %d;\n" % numVerts)

		# Write out the list of vertices for the object
		f.write("\n\t// List of vertices for object %s" % (nmesh.name))
		f.write("\n\tGLfloat vertices[] = {")
		for vertex in vertices :
			f.write("\n\t\t%f,\t%f,\t%f,\t1.0000," % (vertex.co.x, vertex.co.y, vertex.co.z) )
			f.write("\t\t// index : %d" % (vertex.index) )
		f.write("\n\t};")
		f.write("\n\t%s.vbo.bulk_init_vertices (numVertices, (vector4f *)vertices);\n\n" % (nmesh.name))


		# Write out the texture coordinates for the object
		if nmesh.hasFaceUV():
			f.write("\n\t// List of texture_coords for object %s" % (nmesh.name))
			f.write("\n\tGLfloat textures[] = {")
			for vertex in vertices :
				f.write("\n\t\t%f,\t%f," % (vertex.uvco.x, vertex.uvco.y) )
				f.write("\t\t// index : %d" % (vertex.index) )
			f.write("\n\t};")
			f.write("\n\t%s.vbo.bulk_init_textures (numVertices, (vector2f *)textures);\n\n" % (nmesh.name))


		# Write out the normals for the object
		f.write("\n\t// List of normals for object %s" % (nmesh.name))
		f.write("\n\tGLfloat normals[] = {")
		for vertex in vertices :
			f.write("\n\t\t%f,\t%f,\t%f," % (vertex.no.x, vertex.no.y, vertex.no.z) )
			f.write("\t\t// index : %d" % (vertex.index) )
		f.write("\n\t};")
		f.write("\n\t%s.vbo.bulk_init_normals (numVertices, (vector3f *)normals);\n\n" % (nmesh.name))


		numFaces = len(nmesh.faces)
		f.write("\n\tint numFaces = %d;\n" % numFaces)

		# Write out the indices to form each face of the object
		f.write("\n\tGLuint indices[] = {")
		for face in nmesh.faces:
			f.write("\n\t\t")
			for vertex in face.v:
				f.write("%d, " % vertex.index)
		f.write("\n\t};")
		f.write("\n\t%s.vbo.bulk_init_indices (numFaces, (GLuint *)indices);\n\n" % (nmesh.name))

		f.write("\n\treturn;")
		f.write("\n}")
	
		obj_index += 1


	f.write("\n\nvoid initialize_all_models () {")
	for obj in objects:
		nmesh = NMesh.GetRawFromObject(obj.name)
		f.write("\n\n\t%s.initialize (make_%s_vbo_arrays);" % (nmesh.name, nmesh.name))
		f.write("\n\t%s.setTexture (\"./cube_texture_test.png\", PNG);" % nmesh.name)
		f.write("\n\t%s.setColor (0.2, 0.3, 0.4, 1.0);" % nmesh.name)
	f.write("\n\n\treturn;\n}\n")

	f.write("\n\nvoid ready_all_models_for_render () {")
	for obj in objects:
		nmesh = NMesh.GetRawFromObject(obj.name)
		f.write("\n\t%s.make_ready_for_render ();" % nmesh.name)
	f.write("\n\n\treturn;\n}\n\n")

	header_file.write("\n\n#endif\n\n")
		
	print "Export complete"
	
	f.close()


Blender.Window.FileSelector(save_opengl, 'Export Wavefront OBJ', newFName('test_export'))
