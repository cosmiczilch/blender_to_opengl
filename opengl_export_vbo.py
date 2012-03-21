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
from Blender import Object, NMesh, Mesh
from Blender import Armature
	
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
	dup_vertex_index = -1

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
	bone_file = open(filename+".bone", "w")
	
	print "File %s created and opened. Now exporting..." % filename
	
	# Write all the preprocessors in the header file required to
	# make it work w/ vbo_Utilities.h :
	header_file.write("#ifndef MODEL_H")
	header_file.write("\n#define MODEL_H")

	header_file.write("\n\n#include <GL/gl.h>")
	header_file.write("\n#include <GL/glu.h>")
	header_file.write("\n\n#include \"Transformation.h\"")
	header_file.write("\n\n#include \"vbo_Utilities.h\"")
	header_file.write("\n\n#include \"bone.h\"")

	header_file.write("\n\n// The following is the list of objects that will be exported :")
	# The actual object names and their estern declarations will be written out in the loop below

	f.write("#include \"%s.h\"\n\n" % filename)

	# Which object to export
	# currently all objects (meshes only - see below)
	objects = [ob for ob in Object.GetSelected() if ob.getType() == 'Mesh']
	
	obj_index = 0
	for obj in objects:
		nmesh = NMesh.GetRawFromObject(obj.name)
	
		header_file.write("\n\nextern CVBO_Model %s;" % (nmesh.name))

		f.write("\n// Object: %s" % (nmesh.name))
		f.write("\nCVBO_Model %s;" % (nmesh.name))
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
						# get a new temp vert of type MyVert
						newVert = MyVert(0.0, 0.0, 0.0)

						refCount_for_vertices.append(1)

						# Copy over relevant stuff to newVert
						newVert.co = Co(vertices[vertex_idx].co.x, vertices[vertex_idx].co.y, vertices[vertex_idx].co.z)

						newVert.index = vertices[vertex_idx].index
						newVert.dup_vertex_index = vertices[vertex_idx].index

						newVert.no = No(vertices[vertex_idx].no.x, vertices[vertex_idx].no.y, vertices[vertex_idx].no.z)

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
		f.write("\n\t%s.bulk_init_vertices (numVertices, (vec4 *)vertices);\n\n" % (nmesh.name))


		# Write out the texture coordinates for the object
		if nmesh.hasFaceUV():
			f.write("\n\t// List of texture_coords for object %s" % (nmesh.name))
			f.write("\n\tGLfloat textures[] = {")
			for vertex in vertices :
				f.write("\n\t\t%f,\t%f," % (vertex.uvco.x, vertex.uvco.y) )
				f.write("\t\t// index : %d" % (vertex.index) )
			f.write("\n\t};")
			f.write("\n\t%s.bulk_init_textures (numVertices, (vec2 *)textures);\n\n" % (nmesh.name))


		# Write out the normals for the object
		f.write("\n\t// List of normals for object %s" % (nmesh.name))
		f.write("\n\tGLfloat normals[] = {")
		for vertex in vertices :
			f.write("\n\t\t%f,\t%f,\t%f," % (vertex.no.x, vertex.no.y, vertex.no.z) )
			f.write("\t\t// index : %d" % (vertex.index) )
		f.write("\n\t};")
		f.write("\n\t%s.bulk_init_normals (numVertices, (vec3 *)normals);\n\n" % (nmesh.name))


		numFaces = 0
		for face in nmesh.faces:
			numFaces = numFaces + 1
			if len(face.v) == 4:		# , because quads will be exported as 2 triangles (see below)
				numFaces = numFaces + 1
		f.write("\n\tint numFaces = %d;\n" % numFaces)

		# Write out the indices to form each face of the object
		f.write("\n\tGLuint indices[] = {")
		for face in nmesh.faces:
			f.write("\n\t\t")
			f.write("%d, " % face.v[0].index)
			f.write("%d, " % face.v[1].index)
			f.write("%d, " % face.v[2].index)
			if len(face.v) == 4:
				f.write("\n\t\t")
				f.write("%d, " % face.v[3].index)
				f.write("%d, " % face.v[0].index)
				f.write("%d, " % face.v[2].index)
		f.write("\n\t};")
		f.write("\n\t%s.bulk_init_indices (numFaces, (GLuint *)indices);\n\n" % (nmesh.name))


		#translation
		locx = 0;
		locy = 0;
		locz = 0;
		if obj.LocX > 0.0001 or obj.LocX < -0.0001:
			locx = obj.LocX
		if obj.LocY > 0.0001 or obj.LocY < -0.0001:
			locy = obj.LocY
		if obj.LocZ > 0.0001 or obj.LocZ < -0.0001:
			locz = obj.LocZ
		
		f.write("\n\t%s.locX = %f;" % (nmesh.name, locx))
		f.write("\n\t%s.locY = %f;" % (nmesh.name, locy))
		f.write("\n\t%s.locZ = %f;" % (nmesh.name, locz))


		f.write("\n\treturn;")
		f.write("\n}")

		# Bone stuff
		
		mesh = Mesh.Get(obj.name)
		obj.link(mesh)
		f.write("\n\n// Object : %s " % (mesh.name))

		numRealVerts = len(mesh.verts)

		armatures = Armature.Get()	# type: dict
		armature_names = armatures.keys()
		for armature_name in armature_names:
			f.write("\n// Armature %s, being used by %d users" % (armature_name, armatures[armature_name].users) )
			if armatures[armature_name].users > 0:		# being used by at least 1 user (helps discard deleted armatures which are (for some reason) still lying around in Blender)
				armature = armatures[armature_name]
				bones = armature.bones		# type: dict
				bone_names = bones.keys()
				for bone_name in bone_names:				# loop over all bones
					bone = bones[bone_name]
					f.write("\n\nBone %s;" % bone.name)
					header_file.write("\nextern Bone %s;" % bone.name)
					
					f.write("\n\nvoid init_%s_bone_influences () {" % bone.name)
					f.write("\n\tInfluence influences[] = {")


					num_influences = 0
					for vertex_idx in range(numVerts):		# loop over all vertices, looking for The bone's influences
						# bone_file.write("\nindex : %d " % (vertex_idx))
						if vertex_idx < numRealVerts:
							for influence in mesh.getVertexInfluences(vertex_idx):
								if influence[0] == bone.name:
									# bone_file.write("\n %s, %f" % (influence[0], influence[1]))
									f.write("\n\t\tInfluence(%d, %f)," % (vertex_idx, influence[1]))
									num_influences = num_influences + 1
						elif vertex_idx >= numRealVerts:
							for influence in mesh.getVertexInfluences(vertices[vertex_idx].dup_vertex_index):
								if influence[0] == bone.name:
									# bone_file.write("\n %s, %f" % (influence[0], influence[1]))
									f.write("\n\t\tInfluence(%d, %f)," % (vertex_idx, influence[1]))
									num_influences = num_influences + 1

					f.write("\n\t};")
					f.write("\n\n\t%s.bulkInitInfluences (%d, influences);" % (bone.name, num_influences))
					f.write("\n\t%s.name = \"%s\";" % (bone.name, bone.name))
					f.write("\n\n\treturn;")
					f.write("\n};\n")
				
	
		obj_index += 1


	header_file.write("\n\nvoid initialize_all_models ();")
	header_file.write("\nvoid ready_all_models_for_render ();")

	f.write("\n\nvoid initialize_all_models () {")
	for obj in objects:
		nmesh = NMesh.GetRawFromObject(obj.name)
		f.write("\n\n\tmake_%s_vbo_arrays ();" % (nmesh.name))
		f.write("\n\t%s.setTexture (\"./cube_texture_test.png\", PNG);" % nmesh.name)
		f.write("\n\t%s.setMatColor (0.2, 0.3, 0.4, 1.0);" % nmesh.name)
		# Bone stuff : 
		armatures = Armature.Get()	# type: dict
		armature_names = armatures.keys()
		for armature_name in armature_names:
			if armatures[armature_name].users > 0:		# being used by at least 1 user (helps discard deleted armatures which are (for some reason) still lying around in Blender)
				armature = armatures[armature_name]
				bones = armature.bones		# type: dict
				bone_names = bones.keys()
				for bone_name in bone_names:				# loop over all bones
					bone = bones[bone_name]
					f.write("\n\tinit_%s_bone_influences ();" % bone.name)
					f.write("\n\t%s.setVBO (&%s);" % (bone.name, obj.name) )
					f.write("\n\t%s.addBone (&%s);" % (obj.name, bone.name) )





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
